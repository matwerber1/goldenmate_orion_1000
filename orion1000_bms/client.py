from __future__ import annotations

import socket
import time
from dataclasses import dataclass, field
from typing import Final, Optional, Callable, TypeAlias
import logging

from orion1000_bms.protocol import (
    build_voltage_request,
    build_current_status_request,
    build_capacity_status_request,
    build_battery_id_request,
    build_mos_control_allow_discharge,
    build_mos_control_disable_discharge,
    build_mos_control_allow_charge,
    build_mos_control_disable_charge,
    VoltageData,
    CurrentStatusData,
    CapacityData,
    BatteryIdData,
)
from .exceptions import (
    BMSConnectionError,
    BMSProtocolError,
    BMSReadTimeout,
    BMSWriteTimeout,
    BMSError,
)

log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class BMSConfig:
    host: str
    port: int
    addr: int = 0x01
    connect_timeout_s: float = 3.0
    read_timeout_s: float = 5.0
    write_timeout_s: float = 5.0
    linger_close_s: float = 0.2
    first_wake_delay_s: float = 0.35
    poll_gap_s: float = 0.15
    max_retries: int = 3
    backoff_base_s: float = 0.4
    backoff_max_s: float = 2.0
    jitter_s: float = 0.05
    persistent: bool = False


_SockFactory: TypeAlias = Callable[[], socket.socket]


def _default_socket_factory() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return s


class Orion1000BMS:
    def __init__(
        self,
        config: BMSConfig,
        sock_factory: _SockFactory | None = None,
    ) -> None:
        log.debug("Initializing Orion 1000 BMS client")
        self._cfg: Final[BMSConfig] = config
        self._sock_factory: Final[_SockFactory] = (
            sock_factory or _default_socket_factory
        )
        self._last_request_time: float = 0.0
        log.info(
            "Orion1000BMS initialized for %s:%s (addr=0x%02X)",
            self._cfg.host,
            self._cfg.port,
            self._cfg.addr,
        )

    def _enforce_min_gap(self) -> None:
        # Ensure at least 150 ms between any two requests
        now = time.monotonic()
        elapsed = now - self._last_request_time
        min_gap = max(0.15, self._cfg.poll_gap_s)
        if elapsed < min_gap:
            sleep_s = min_gap - elapsed
            log.debug(
                f"Throttling: sleeping {sleep_s:.3f}s to enforce inter-request gap"
            )
            time.sleep(sleep_s)
        self._last_request_time = time.monotonic()

    def _open_socket(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return s

    def _read_exact(self, s: socket.socket, n: int, timeout: float) -> bytes:
        buf = bytearray()
        s.settimeout(timeout)
        while len(buf) < n:
            try:
                chunk = s.recv(n - len(buf))
            except socket.timeout as e:
                raise BMSReadTimeout("read timed out") from e
            except OSError as e:
                raise BMSConnectionError(f"read failed: {e}") from e
            if not chunk:
                raise BMSConnectionError("connection closed by peer")
            buf.extend(chunk)
        return bytes(buf)

    def _read_reply_frame(self, s: socket.socket) -> bytes:
        # Sync to start byte 0xEA
        s.settimeout(self._cfg.read_timeout_s)
        while True:
            try:
                b = s.recv(1)
            except socket.timeout as e:
                raise BMSReadTimeout("read timed out") from e
            except OSError as e:
                raise BMSConnectionError(f"read failed: {e}") from e
            if not b:
                raise BMSConnectionError("connection closed by peer")
            if b[0] == 0xEA:
                break
        # Read next 3 bytes of header
        rest_hdr = self._read_exact(s, 3, self._cfg.read_timeout_s)
        hdr = b + rest_hdr
        if hdr[1] != 0xD1:
            raise BMSProtocolError(f"bad preamble: {hdr!r}")
        total_to_follow = hdr[3]
        rest = self._read_exact(s, total_to_follow, self._cfg.read_timeout_s)
        frame = hdr + rest
        log.debug("Raw frame: " + " ".join(f"{x:02X}" for x in frame))
        return frame

    def _request_once(self, payload: bytes) -> bytes:
        self._enforce_min_gap()
        s = self._open_socket()
        try:
            s.settimeout(self._cfg.connect_timeout_s)
            log.debug(f"Connecting to {self._cfg.host}:{self._cfg.port}")
            s.connect((self._cfg.host, self._cfg.port))
            # write
            s.settimeout(self._cfg.write_timeout_s)
            log.debug("Sending request: " + " ".join(f"{x:02X}" for x in payload))
            s.sendall(payload)
            # small settle
            time.sleep(0.05)
            # read reply
            frame = self._read_reply_frame(s)
            return frame
        except (socket.timeout, OSError) as e:
            raise BMSConnectionError(str(e)) from e
        finally:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                s.close()
            except Exception:
                pass

    def _request_with_retries(self, request: bytes, retries: int) -> bytes:
        attempts = max(0, retries)
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= attempts:
            attempt += 1
            try:
                log.info(
                    f"Attempt {attempt}/{attempts + 1} sending request to {self._cfg.host}:{self._cfg.port}"
                )
                return self._request_once(request)
            except (BMSReadTimeout, BMSWriteTimeout, BMSConnectionError) as e:
                last_exc = e
                if attempt <= attempts:
                    log.warning(f"Request attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(
                        min(
                            self._cfg.backoff_max_s,
                            self._cfg.backoff_base_s * (2 ** (attempt - 1)),
                        )
                    )
                else:
                    log.error(f"All {attempts + 1} attempts failed: {e}")
                    break
        assert last_exc is not None
        raise last_exc

    def read_voltage(self, retries: int = 3) -> VoltageData:
        req = build_voltage_request(self._cfg.addr)
        log.info("Reading voltage")
        frame = self._request_with_retries(req, retries)
        return VoltageData.from_bytes(frame)

    def read_current_status(self, retries: int = 3) -> CurrentStatusData:
        log.info("Reading current status")
        req = build_current_status_request(self._cfg.addr)
        frame = self._request_with_retries(req, retries)
        return CurrentStatusData.from_bytes(frame)

    def read_capacity(self, retries: int = 3) -> CapacityData:
        log.info("Reading capacity/SOC")
        req = build_capacity_status_request(self._cfg.addr)
        frame = self._request_with_retries(req, retries)
        return CapacityData.from_bytes(frame)

    def read_battery_id(self, retries: int = 3) -> BatteryIdData:
        log.info("Reading battery ID")
        req = build_battery_id_request(self._cfg.addr)
        frame = self._request_with_retries(req, retries)
        return BatteryIdData.from_bytes(frame)

    def allow_discharge(self, retries: int = 3) -> None:
        log.info("Sending: enable discharge MOS")
        req = build_mos_control_allow_discharge(self._cfg.addr)
        _ = self._request_with_retries(req, retries)

    def disable_discharge(self, retries: int = 3) -> None:
        log.info("Sending: disable discharge MOS")
        req = build_mos_control_disable_discharge(self._cfg.addr)
        _ = self._request_with_retries(req, retries)

    def allow_charge(self, retries: int = 3) -> None:
        log.info("Sending: enable charge MOS")
        req = build_mos_control_allow_charge(self._cfg.addr)
        _ = self._request_with_retries(req, retries)

    def disable_charge(self, retries: int = 3) -> None:
        log.info("Sending: disable charge MOS")
        req = build_mos_control_disable_charge(self._cfg.addr)
        _ = self._request_with_retries(req, retries)

"""TCP transport implementation using pyserial."""

import time
import logging
from typing import Optional
import serial
from ..protocol.constants import START, END
from ..exceptions import TransportError, TimeoutError
from ..logging import get_logger, log_frame_tx, log_frame_rx
from .base import BaseTransport


class TcpTransport(BaseTransport):
    """TCP transport for BMS communication using pyserial."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 3.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize TCP transport.

        Args:
            host: TCP server hostname or IP
            port: TCP server port
            connect_timeout: Connection timeout (unused with pyserial)
            read_timeout: Read timeout in seconds
            max_retries: Maximum number of retries on timeout
        """
        super().__init__(max_retries=max_retries)
        self.host = host
        self.port = port
        self.read_timeout = read_timeout
        self._serial: Optional[serial.Serial] = None
        self._logger = get_logger(__name__)

    def open_if_needed(self) -> None:
        """Open connection if not already open."""
        if self._serial is None:
            try:
                url = f"socket://{self.host}:{self.port}"
                self._serial = serial.serial_for_url(
                    url,
                    timeout=self.read_timeout,
                    inter_byte_timeout=0.2,
                    write_timeout=1.0,
                )
                self._logger.debug("Connected to %s:%d", self.host, self.port)
            except Exception as e:
                raise TransportError(
                    f"Connection failed to {self.host}:{self.port}: {e}"
                )

    def close(self) -> None:
        """Close the connection."""
        if self._serial:
            self._serial.close()
            self._serial = None

    def _send_request_impl(
        self, payload: bytes, *, timeout: float | None = None
    ) -> bytes:
        """Implementation-specific request sending.

        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout override

        Returns:
            Response frame bytes
        """
        self.open_if_needed()

        if not self._serial:
            raise TransportError("Serial connection not open")

        try:
            # Clear buffers and send request
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

            log_frame_tx(self._logger, payload)
            self._serial.write(payload)
            self._serial.flush()

            # Read response
            response = self._read_frame(timeout or self.read_timeout)
            log_frame_rx(self._logger, response)

            # Inter-request spacing per BMS protocol
            time.sleep(0.20)

            return response
        except Exception as e:
            if "timeout" in str(e).lower():
                raise TimeoutError("Request timeout")
            raise TransportError(f"Transport error: {e}")

    def _read_exact(self, n: int, *, timeout_s: float = 1.0) -> bytes:
        """Read exactly n bytes or raise TimeoutError."""
        if not self._serial:
            raise TransportError("Serial connection not open")

        end_by = time.monotonic() + timeout_s
        buf = bytearray()
        while len(buf) < n:
            if time.monotonic() > end_by:
                raise TimeoutError(f"Timeout reading {n} bytes (got {len(buf)})")
            chunk = self._serial.read(n - len(buf))
            if chunk:
                buf.extend(chunk)
            else:
                time.sleep(0.005)
        return bytes(buf)

    def _read_frame(self, timeout: float) -> bytes:
        """Read one complete frame with validation."""
        # Read header: [START PID addr len]
        header = self._read_exact(4, timeout_s=timeout)
        if header[0] != START:
            raise TransportError(f"Bad start byte: {header[0]:#04x}")

        length = header[3]
        if length < 4:
            raise TransportError(f"Length too small: {length}")

        # Read payload: data + checksum + end
        payload = self._read_exact(length, timeout_s=timeout)
        if payload[-1] != END:
            raise TransportError("Missing end byte")

        return header + payload

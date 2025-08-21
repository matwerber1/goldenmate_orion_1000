"""BMS client for synchronous communication."""

from __future__ import annotations
import threading
import time
from typing import TYPE_CHECKING, cast

from .commands.base import BaseCommand, BaseResponse
from .commands.registry import COMMANDS, CommandId
from .commands import (
    VoltageRequest,
    VoltageResponse,
    CurrentStatusRequest,
    CurrentStatusResponse,
    CapacityStatusRequest,
    CapacityStatusResponse,
    SerialNumberRequest,
    SerialNumberResponse,
    AllowDischargeRequest,
    DisallowDischargeRequest,
    AllowChargeRequest,
    DisallowChargeRequest,
    MosControlResponse,
)
from .exceptions import UnsupportedCommandError
from .logging import get_logger
from .protocol.codec import build_frame
from .protocol.constants import PRODUCT_ID_DEFAULT, COMMAND_HIGH

if TYPE_CHECKING:
    from .transport.base import AbstractTransport


class BmsClient:
    """Synchronous BMS client with request spacing enforcement."""

    def __init__(
        self,
        transport: AbstractTransport,
        *,
        product_id: int = PRODUCT_ID_DEFAULT,
        address: int = 0x01,
        min_spacing_s: float = 1,
    ) -> None:
        """Initialize BMS client.

        Args:
            transport: Transport layer for communication
            product_id: BMS product ID
            address: BMS device address
            min_spacing_s: Minimum spacing between requests in seconds
        """
        self._transport = transport
        self._product_id = product_id
        self._address = address
        self._min_spacing_s = min_spacing_s
        self._lock = threading.Lock()
        self._last_request_time = 0.0
        self._logger = get_logger(__name__)

    def request(
        self, req: BaseCommand, *, timeout: float | None = None
    ) -> BaseResponse:
        """Send request and return parsed response.

        Args:
            req: Command request to send
            timeout: Optional timeout override

        Returns:
            Parsed response object

        Raises:
            UnsupportedCommandError: If command not in registry
            TransportError: On communication failure
        """
        with self._lock:
            # Enforce minimum spacing
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_spacing_s:
                time.sleep(self._min_spacing_s - elapsed)

            # Look up command spec
            try:
                cmd_id = CommandId(req.command_id)
            except ValueError:
                self._logger.warning("Unknown command ID: 0x%04x", req.command_id)
                raise UnsupportedCommandError(f"Unknown command: {req.command_id}")

            if cmd_id not in COMMANDS:
                self._logger.warning("Command not in registry: 0x%04x", req.command_id)
                raise UnsupportedCommandError(f"Unknown command: {req.command_id}")

            self._logger.debug(
                "Sending command 0x%02x to address 0x%02x",
                req.command_id,
                self._address,
            )

            spec = COMMANDS[cmd_id]

            # Build request frame
            cmd_hi = COMMAND_HIGH  # Always 0xFF
            cmd_lo = req.command_id  # Command ID is now the low byte
            payload = req.to_payload()

            request_frame = build_frame(
                self._product_id, self._address, cmd_hi, cmd_lo, payload
            )

            # Send request and get response
            response_bytes = self._transport.send_request(
                request_frame, timeout=timeout
            )

            # Parse response
            from .protocol.codec import decode

            response_frame = decode(response_bytes)

            # Verify response matches request
            if (response_frame.cmd_hi != cmd_hi) or (response_frame.cmd_lo != cmd_lo):
                self._logger.warning(
                    "Response command mismatch: expected 0x%02x%02x, got 0x%02x%02x",
                    cmd_hi,
                    cmd_lo,
                    response_frame.cmd_hi,
                    response_frame.cmd_lo,
                )
                raise UnsupportedCommandError("Response command mismatch")

            # Parse response payload (include command bytes in payload)
            try:
                full_payload = (
                    bytes([response_frame.cmd_hi, response_frame.cmd_lo])
                    + response_frame.payload
                )
                response = spec.resp.from_payload(full_payload)
                self._logger.debug(
                    "Successfully processed command 0x%02x", req.command_id
                )
            except Exception as e:
                self._logger.exception(
                    "Failed to parse response payload for command 0x%02x",
                    req.command_id,
                )
                raise

            self._last_request_time = time.time()
            return response

    def read_voltage_data(self, *, timeout: float | None = None) -> VoltageResponse:
        """Read all cell voltages and temperatures.

        Args:
            timeout: Optional timeout override

        Returns:
            VoltageResponse with all cell voltages and temperatures
        """
        req = VoltageRequest()
        resp = cast(VoltageResponse, self.request(req, timeout=timeout))
        return resp

    def read_current_status(
        self, *, timeout: float | None = None
    ) -> CurrentStatusResponse:
        """Read current and status information.

        Args:
            timeout: Optional timeout override

        Returns:
            CurrentStatusResponse with current and status data
        """
        req = CurrentStatusRequest()
        resp = cast(CurrentStatusResponse, self.request(req, timeout=timeout))
        return resp

    def read_capacity_status(
        self, *, timeout: float | None = None
    ) -> CapacityStatusResponse:
        """Read capacity and status information.

        Args:
            timeout: Optional timeout override

        Returns:
            CapacityStatusResponse with capacity data
        """
        req = CapacityStatusRequest()
        resp = cast(CapacityStatusResponse, self.request(req, timeout=timeout))
        return resp

    def read_serial_number(self, *, timeout: float | None = None) -> str:
        """Read device serial number.

        Args:
            timeout: Optional timeout override

        Returns:
            Device serial number as string
        """
        req = SerialNumberRequest()
        resp = cast(SerialNumberResponse, self.request(req, timeout=timeout))
        return resp.serial_number

    def allow_discharge(self, *, timeout: float | None = None) -> bool:
        """Allow discharge (open discharge MOS).

        Args:
            timeout: Optional timeout override

        Returns:
            True if successful, False otherwise
        """
        req = AllowDischargeRequest()
        resp = cast(MosControlResponse, self.request(req, timeout=timeout))
        return resp.success

    def disallow_discharge(self, *, timeout: float | None = None) -> bool:
        """Disallow discharge (close discharge MOS).

        Args:
            timeout: Optional timeout override

        Returns:
            True if successful, False otherwise
        """
        req = DisallowDischargeRequest()
        resp = cast(MosControlResponse, self.request(req, timeout=timeout))
        return resp.success

    def allow_charge(self, *, timeout: float | None = None) -> bool:
        """Allow charge.

        Args:
            timeout: Optional timeout override

        Returns:
            True if successful, False otherwise
        """
        req = AllowChargeRequest()
        resp = cast(MosControlResponse, self.request(req, timeout=timeout))
        return resp.success

    def disallow_charge(self, *, timeout: float | None = None) -> bool:
        """Disallow charge.

        Args:
            timeout: Optional timeout override

        Returns:
            True if successful, False otherwise
        """
        req = DisallowChargeRequest()
        resp = cast(MosControlResponse, self.request(req, timeout=timeout))
        return resp.success

    def close(self) -> None:
        """Close the transport connection."""
        self._transport.close()

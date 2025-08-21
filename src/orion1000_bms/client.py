"""BMS client for synchronous communication."""

from __future__ import annotations
import threading
import time
from typing import TYPE_CHECKING, cast

from .commands.base import BaseCommand, BaseResponse
from .commands.registry import COMMANDS, CommandId
from .commands.read_cell_voltage import ReadCellVoltageRequest, ReadCellVoltageResponse
from .commands.read_current import ReadCurrentRequest, ReadCurrentResponse
from .commands.read_total_voltage import (
    ReadTotalVoltageRequest,
    ReadTotalVoltageResponse,
)
from .exceptions import UnsupportedCommandError
from .logging import get_logger
from .protocol.codec import build_frame
from .protocol.constants import PRODUCT_ID_DEFAULT

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
        min_spacing_s: float = 0.2,
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
            cmd_id = CommandId(req.command_id)
            if cmd_id not in COMMANDS:
                raise UnsupportedCommandError(f"Unknown command: {req.command_id}")

            spec = COMMANDS[cmd_id]

            # Build request frame
            cmd_hi = (req.command_id >> 8) & 0xFF
            cmd_lo = req.command_id & 0xFF
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
                raise UnsupportedCommandError("Response command mismatch")

            # Parse response payload
            response = spec.resp.from_payload(response_frame.payload)

            self._last_request_time = time.time()
            return response

    def read_total_voltage(self, *, timeout: float | None = None) -> float:
        """Read total pack voltage.

        Args:
            timeout: Optional timeout override

        Returns:
            Total voltage in volts
        """
        req = ReadTotalVoltageRequest()
        resp = cast(ReadTotalVoltageResponse, self.request(req, timeout=timeout))
        return resp.voltage

    def read_current(self, *, timeout: float | None = None) -> float:
        """Read pack current.

        Args:
            timeout: Optional timeout override

        Returns:
            Current in amperes
        """
        req = ReadCurrentRequest()
        resp = cast(ReadCurrentResponse, self.request(req, timeout=timeout))
        return resp.current

    def read_cell_voltage(
        self, cell_index: int, *, timeout: float | None = None
    ) -> float:
        """Read individual cell voltage.

        Args:
            cell_index: Cell index (0-based)
            timeout: Optional timeout override

        Returns:
            Cell voltage in volts
        """
        req = ReadCellVoltageRequest(cell_index=cell_index)
        resp = cast(ReadCellVoltageResponse, self.request(req, timeout=timeout))
        return resp.voltage

    def close(self) -> None:
        """Close the transport connection."""
        self._transport.close()

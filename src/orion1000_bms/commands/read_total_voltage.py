"""Read total voltage command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
import struct
from typing import TYPE_CHECKING
from .registry import CommandId, COMMANDS
from .base import CommandSpec

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .base import BaseCommand, BaseResponse


@dataclass(slots=True)
class ReadTotalVoltageRequest:
    """Request to read total pack voltage."""

    command_id: int = CommandId.READ_TOTAL_VOLTAGE
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for read commands)."""
        return b""


@dataclass(slots=True, frozen=True)
class ReadTotalVoltageResponse:
    """Response containing total pack voltage."""

    voltage: float  # Voltage in volts

    @classmethod
    def from_payload(cls, payload: bytes) -> ReadTotalVoltageResponse:
        """Parse voltage from payload bytes.

        Args:
            payload: 2-byte payload containing voltage in 0.1V units

        Returns:
            ReadTotalVoltageResponse with voltage in volts
        """
        if len(payload) != 2:
            logger.warning("Invalid payload length for total voltage: %d", len(payload))
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Voltage is big-endian 16-bit unsigned integer in 0.1V units
        voltage_raw = struct.unpack(">H", payload)[0]
        voltage = voltage_raw / 10.0
        logger.debug("Parsed total voltage: %.1fV", voltage)

        return cls(voltage=voltage)


# Register command
COMMANDS[CommandId.READ_TOTAL_VOLTAGE] = CommandSpec(
    req=ReadTotalVoltageRequest,  # type: ignore[arg-type]
    resp=ReadTotalVoltageResponse,  # type: ignore[arg-type]
)

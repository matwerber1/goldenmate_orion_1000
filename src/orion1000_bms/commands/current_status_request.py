"""Current and status request command implementation."""

from __future__ import annotations
import logging
import struct
from dataclasses import dataclass
from typing import List
from .registry import CommandId, COMMANDS
from .base import CommandSpec

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CurrentStatusRequest:
    """Request to read current and status information."""

    command_id: int = CommandId.CURRENT_STATUS_REQUEST
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for current status request)."""
        return b""


@dataclass(slots=True, frozen=True)
class CurrentStatusResponse:
    """Response containing current and status information."""

    status_bits: int  # Status bitfield
    current: float  # Current in amperes (positive=discharge, negative=charge)
    protection_status: int  # Protection status bitfield
    temperatures: List[float]  # 3 temperature probes in Celsius
    mos_states: int  # MOSFET states bitfield
    version: int  # Hardware/firmware version
    fault_flags: int  # Fault flags bitfield

    @classmethod
    def from_payload(cls, payload: bytes) -> CurrentStatusResponse:
        """Parse current and status data from payload bytes.

        Args:
            payload: 13-byte payload (2 cmd bytes + 10 data bytes)

        Returns:
            CurrentStatusResponse with parsed data
        """
        if len(payload) != 15:
            logger.warning(
                "Invalid payload length for current status response: %d", len(payload)
            )
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse fields according to spec
        status_bits = data[0]
        current_raw = struct.unpack(">h", data[1:3])[0]  # signed int16
        current = current_raw / 10.0  # Convert 0.1A to A
        protection_status = data[3]

        # Parse 3 temperature probes (6 bytes, 2 bytes each, in 0.1°C)
        temperatures = []
        for i in range(3):
            temp_raw = struct.unpack(">h", data[4 + i * 2 : 4 + (i * 2) + 2])[
                0
            ]  # signed int16
            temp = temp_raw / 10.0  # Convert 0.1°C to °C
            temperatures.append(temp)

        mos_states = data[10]
        version = data[11]
        fault_flags = data[12] if len(data) > 12 else 0

        logger.debug(
            "Parsed current status response: current=%.1fA, status=0x%02x",
            current,
            status_bits,
        )

        return cls(
            status_bits=status_bits,
            current=current,
            protection_status=protection_status,
            temperatures=temperatures,
            mos_states=mos_states,
            version=version,
            fault_flags=fault_flags,
        )


# Register command
COMMANDS[CommandId.CURRENT_STATUS_REQUEST] = CommandSpec(
    req=CurrentStatusRequest, resp=CurrentStatusResponse
)

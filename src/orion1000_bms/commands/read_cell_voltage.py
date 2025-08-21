"""Read cell voltage command implementation."""

from __future__ import annotations
from dataclasses import dataclass
import struct
from typing import List
from .registry import CommandId, COMMANDS
from .base import CommandSpec


@dataclass(slots=True)
class ReadCellVoltageRequest:
    """Request to read individual cell voltage."""

    command_id: int = CommandId.READ_CELL_VOLTAGE
    address: int = 0x01
    cell_index: int = 0  # Cell index (0-based)

    def to_payload(self) -> bytes:
        """Convert to payload bytes containing cell index."""
        return struct.pack(">B", self.cell_index)


@dataclass(slots=True, frozen=True)
class ReadCellVoltageResponse:
    """Response containing cell voltage."""

    cell_index: int
    voltage: float  # Voltage in volts

    @classmethod
    def from_payload(cls, payload: bytes) -> ReadCellVoltageResponse:
        """Parse cell voltage from payload bytes.

        Args:
            payload: 3-byte payload containing cell index and voltage

        Returns:
            ReadCellVoltageResponse with cell index and voltage
        """
        if len(payload) != 3:
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # First byte is cell index, next 2 bytes are voltage in 0.001V units
        cell_index = payload[0]
        voltage_raw = struct.unpack(">H", payload[1:3])[0]
        voltage = voltage_raw / 1000.0

        return cls(cell_index=cell_index, voltage=voltage)


# Register command
COMMANDS[CommandId.READ_CELL_VOLTAGE] = CommandSpec(
    req=ReadCellVoltageRequest, resp=ReadCellVoltageResponse
)

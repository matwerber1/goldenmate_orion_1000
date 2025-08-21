"""Voltage request command implementation."""

from __future__ import annotations
import logging
import struct
from dataclasses import dataclass
from typing import List
from .registry import CommandId, COMMANDS
from .base import CommandSpec

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VoltageRequest:
    """Request to read all cell voltages and temperatures."""

    command_id: int = CommandId.VOLTAGE_REQUEST
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for voltage request)."""
        return b""


@dataclass(slots=True, frozen=True)
class VoltageResponse:
    """Response containing cell voltages and temperatures."""

    cell_voltages: List[float]  # 16 cell voltages in volts
    temperatures: List[float]  # 3 temperature probes in Celsius
    system_string_count: int  # Number of battery strings

    @classmethod
    def from_payload(cls, payload: bytes) -> VoltageResponse:
        """Parse voltage data from payload bytes.

        Args:
            payload: 35-byte payload (2 cmd bytes + 32 cell voltages + 6 temperatures + 1 string count)

        Returns:
            VoltageResponse with parsed data
        """
        if len(payload) != 41:
            logger.warning(
                "Invalid payload length for voltage response: %d", len(payload)
            )
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse 16 cell voltages (32 bytes, 2 bytes each, in mV)
        cell_voltages = []
        for i in range(16):
            voltage_raw = struct.unpack(">H", data[i * 2 : (i * 2) + 2])[0]
            voltage = voltage_raw / 1000.0  # Convert mV to V
            cell_voltages.append(voltage)

        # Parse 3 temperature probes (6 bytes, 2 bytes each, in 0.1°C)
        temperatures = []
        for i in range(3):
            temp_raw = struct.unpack(">h", data[32 + i * 2 : 32 + (i * 2) + 2])[
                0
            ]  # signed int16
            temp = temp_raw / 10.0  # Convert 0.1°C to °C
            temperatures.append(temp)

        # Parse system string count (1 byte)
        system_string_count = data[38]

        logger.debug(
            "Parsed voltage response: %d cells, %d temps, %d strings",
            len(cell_voltages),
            len(temperatures),
            system_string_count,
        )

        return cls(
            cell_voltages=cell_voltages,
            temperatures=temperatures,
            system_string_count=system_string_count,
        )


# Register command
COMMANDS[CommandId.VOLTAGE_REQUEST] = CommandSpec(
    req=VoltageRequest, resp=VoltageResponse
)

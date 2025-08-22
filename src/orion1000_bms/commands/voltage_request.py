"""Voltage request command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List
from .registry import CommandId, COMMANDS
from .base import CommandSpec, ResponseBase
from .parsing_utils import parse_big_endian_uint16

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
class VoltageResponse(ResponseBase):
    """Response containing cell voltages and system metadata."""

    cell_voltages: List[float]  # Variable number of cell voltages in volts
    cell_count_in_packet: int  # Number of cells in this packet
    temp_probe_count: int  # Number of temperature probes
    total_system_cells: int  # Total cells in the system

    @classmethod
    def from_payload(cls, payload: bytes) -> VoltageResponse:
        """Parse voltage data from payload bytes.

        Args:
            payload: Variable length payload with command bytes + metadata + cell voltages

        Returns:
            VoltageResponse with parsed data
        """
        # Validate minimum payload length: cmd(2) + cell_count(1) + temp_probes(1) + total_cells(1) = 5 bytes
        cls.validate_minimum_payload_length(payload, 3)

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse metadata fields according to new spec
        cell_count_in_packet = data[0]  # Byte 7 in spec
        temp_probe_count = data[1]  # Byte 8 in spec
        total_system_cells = data[2]  # Byte 9 in spec

        # Calculate expected cell voltage data length
        expected_voltage_bytes = cell_count_in_packet * 2
        min_required_bytes = 3 + expected_voltage_bytes  # metadata + voltages

        if len(data) < min_required_bytes:
            raise ValueError(
                f"Insufficient data for {cell_count_in_packet} cells: "
                f"expected {min_required_bytes}, got {len(data)}"
            )

        # Parse cell voltages (2 bytes each, in mV, big-endian)
        cell_voltages = []
        for i in range(cell_count_in_packet):
            offset = 3 + (i * 2)  # Skip metadata bytes
            voltage_raw = parse_big_endian_uint16(data, offset)
            voltage = voltage_raw / 1000.0  # Convert mV to V
            cell_voltages.append(voltage)

        logger.debug(
            "Parsed voltage response: %d cells in packet, %d temp probes, %d total system cells",
            cell_count_in_packet,
            temp_probe_count,
            total_system_cells,
        )

        return cls(
            cell_voltages=cell_voltages,
            cell_count_in_packet=cell_count_in_packet,
            temp_probe_count=temp_probe_count,
            total_system_cells=total_system_cells,
        )


# Register command
COMMANDS[CommandId.VOLTAGE_REQUEST] = CommandSpec(
    req=VoltageRequest, resp=VoltageResponse
)

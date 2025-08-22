"""Capacity and status request command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, Any
from .registry import CommandId, COMMANDS
from .base import CommandSpec, ResponseBase
from .parsing_utils import parse_big_endian_uint16, parse_tagged_data

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CapacityStatusRequest:
    """Request to read capacity and status information."""

    command_id: int = CommandId.CAPACITY_STATUS_REQUEST
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for capacity status request)."""
        return b""


@dataclass(slots=True, frozen=True)
class CapacityStatusResponse(ResponseBase):
    """Response containing capacity and status information."""

    soc: int  # State of charge (%)
    cycle_count: int  # Cycle count
    design_capacity_high: int  # Design capacity high 16 bits
    design_capacity_low: int  # Design capacity low 16 bits
    full_charge_capacity_high: int  # Full charge capacity high 16 bits
    full_charge_capacity_low: int  # Full charge capacity low 16 bits
    remaining_capacity_high: int  # Remaining capacity high 16 bits
    remaining_capacity_low: int  # Remaining capacity low 16 bits
    remaining_discharge_time: int  # Remaining discharge time in minutes
    remaining_charge_time: int  # Remaining charge time in minutes
    charge_interval_current: int  # Current charge interval in hours
    charge_interval_max: int  # Max charge interval in hours
    pack_voltage: float  # Pack voltage in volts (10mV units)
    max_cell_voltage: float  # Max cell voltage in volts (1mV units)
    min_cell_voltage: float  # Min cell voltage in volts (1mV units)
    hardware_version: int  # Hardware version
    scheme_id: int  # Scheme ID
    reserved: bytes  # Reserved bytes

    @classmethod
    def from_payload(cls, payload: bytes) -> CapacityStatusResponse:
        """Parse capacity and status data from payload bytes.

        Args:
            payload: Variable length payload with command bytes + tagged data

        Returns:
            CapacityStatusResponse with parsed data
        """
        # Validate minimum payload length
        cls.validate_minimum_payload_length(
            payload, 49
        )  # Adjusted based on actual BMS response

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse tagged data section (bytes 7-36 in spec)
        tag_map = {
            0x01: ("soc", 1),
            0x02: ("cycle_count", 2),
            0x03: ("design_capacity_high", 2),
            0x04: ("design_capacity_low", 2),
            0x05: ("full_charge_capacity_high", 2),
            0x06: ("full_charge_capacity_low", 2),
            0x07: ("remaining_capacity_high", 2),
            0x08: ("remaining_capacity_low", 2),
            0x09: ("remaining_discharge_time", 2),
            0x0A: ("remaining_charge_time", 2),
            0x0B: ("charge_interval", 12),  # 2 values: current interval, max interval
            0x0D: ("hardware_version", 1),
        }

        # Parse tagged section (first 30 bytes of data)
        tagged_data = parse_tagged_data(data[:30], tag_map)

        # Extract values with defaults
        soc = tagged_data.get("soc", 0)
        cycle_count = tagged_data.get("cycle_count", 0)
        design_capacity_high = tagged_data.get("design_capacity_high", 0)
        design_capacity_low = tagged_data.get("design_capacity_low", 0)
        full_charge_capacity_high = tagged_data.get("full_charge_capacity_high", 0)
        full_charge_capacity_low = tagged_data.get("full_charge_capacity_low", 0)
        remaining_capacity_high = tagged_data.get("remaining_capacity_high", 0)
        remaining_capacity_low = tagged_data.get("remaining_capacity_low", 0)
        remaining_discharge_time = tagged_data.get("remaining_discharge_time", 0)
        remaining_charge_time = tagged_data.get("remaining_charge_time", 0)
        hardware_version = tagged_data.get("hardware_version", 0)

        # Parse charge interval data (12 bytes)
        charge_interval_data = tagged_data.get("charge_interval", b"\x00" * 12)
        charge_interval_current = (
            parse_big_endian_uint16(charge_interval_data, 0)
            if len(charge_interval_data) >= 2
            else 0
        )
        charge_interval_max = (
            parse_big_endian_uint16(charge_interval_data, 2)
            if len(charge_interval_data) >= 4
            else 0
        )

        # Parse fixed position fields (bytes 48-59 in spec)
        offset = 42  # Skip to byte 48 equivalent in data
        pack_voltage_raw = (
            parse_big_endian_uint16(data, offset) if offset + 1 < len(data) else 0
        )
        pack_voltage = pack_voltage_raw * 0.01  # Convert 10mV to V
        offset += 2

        max_cell_voltage_raw = (
            parse_big_endian_uint16(data, offset) if offset + 1 < len(data) else 0
        )
        max_cell_voltage = max_cell_voltage_raw * 0.001  # Convert 1mV to V
        offset += 2

        min_cell_voltage_raw = (
            parse_big_endian_uint16(data, offset) if offset + 1 < len(data) else 0
        )
        min_cell_voltage = min_cell_voltage_raw * 0.001  # Convert 1mV to V
        offset += 2

        # Skip hardware version (already parsed from tags)
        offset += 1

        scheme_id = data[offset] if offset < len(data) else 0
        offset += 1

        # Reserved bytes
        reserved = (
            data[offset : offset + 3] if offset + 2 < len(data) else b"\x00\x00\x00"
        )

        logger.debug(
            "Parsed capacity status response: SOC=%d%%, pack_voltage=%.2fV",
            soc,
            pack_voltage,
        )

        return cls(
            soc=soc,
            cycle_count=cycle_count,
            design_capacity_high=design_capacity_high,
            design_capacity_low=design_capacity_low,
            full_charge_capacity_high=full_charge_capacity_high,
            full_charge_capacity_low=full_charge_capacity_low,
            remaining_capacity_high=remaining_capacity_high,
            remaining_capacity_low=remaining_capacity_low,
            remaining_discharge_time=remaining_discharge_time,
            remaining_charge_time=remaining_charge_time,
            charge_interval_current=charge_interval_current,
            charge_interval_max=charge_interval_max,
            pack_voltage=pack_voltage,
            max_cell_voltage=max_cell_voltage,
            min_cell_voltage=min_cell_voltage,
            hardware_version=hardware_version,
            scheme_id=scheme_id,
            reserved=reserved,
        )


# Register command
COMMANDS[CommandId.CAPACITY_STATUS_REQUEST] = CommandSpec(
    req=CapacityStatusRequest, resp=CapacityStatusResponse
)

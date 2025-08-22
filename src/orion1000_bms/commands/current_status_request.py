"""Current and status request command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Dict
from .registry import CommandId, COMMANDS
from .base import CommandSpec, ResponseBase
from .parsing_utils import (
    parse_big_endian_uint16,
    parse_temperature,
    extract_bitfield_flags,
)

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
class CurrentStatusResponse(ResponseBase):
    """Response containing current and status information."""

    status_flags: Dict[str, bool]  # Parsed status flags
    current: float  # Current in amperes (10mA units)
    overvoltage_protection: Dict[str, bool]  # OV protection flags
    undervoltage_protection: Dict[str, bool]  # UV protection flags
    temperature_protection: Dict[str, bool]  # Temperature protection flags
    general_protection: Dict[str, bool]  # General protection flags
    temp_probe_count: int  # Number of temperature probes
    temperatures: List[float]  # Temperature readings in Celsius
    software_version: int  # Software version
    mos_state: Dict[str, bool]  # MOS state flags
    failure_status: Dict[str, bool]  # Failure status flags

    @classmethod
    def from_payload(cls, payload: bytes) -> CurrentStatusResponse:
        """Parse current and status data from payload bytes.

        Args:
            payload: Variable length payload with command bytes + status data

        Returns:
            CurrentStatusResponse with parsed data
        """
        # Validate minimum payload length for fixed fields
        cls.validate_minimum_payload_length(payload, 8)  # Basic required fields

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse fields according to new spec (byte positions from spec table)
        offset = 0

        # Byte 7: Status Flags
        status_flags_raw = data[offset]
        status_flags = extract_bitfield_flags(
            status_flags_raw,
            {
                0: "discharge_active",
                1: "charge_active",
                4: "mos_temp_present",
                5: "ambient_temp_present",
            },
        )
        offset += 1

        # Bytes 8-9: Current Value (2 bytes, unsigned, 10mA units)
        current_raw = parse_big_endian_uint16(data, offset)
        current = current_raw * 0.01  # Convert 10mA to A
        offset += 2

        # Byte 10: Over-voltage Protection Status
        ov_protection = extract_bitfield_flags(
            data[offset], {0: "cell_ov", 1: "pack_ov", 4: "full_charge_protection"}
        )
        offset += 1

        # Byte 11: Under-voltage Protection Status
        uv_protection = extract_bitfield_flags(
            data[offset], {0: "cell_uv", 1: "pack_uv"}
        )
        offset += 1

        # Byte 12: Temperature Protection Status
        temp_protection = extract_bitfield_flags(
            data[offset],
            {
                0: "charge_temp",
                1: "discharge_temp",
                2: "mos_over_temp",
                4: "high_temp",
                5: "low_temp",
            },
        )
        offset += 1

        # Byte 13: General Protection Status
        general_protection = extract_bitfield_flags(
            data[offset],
            {
                0: "discharge_short_circuit",
                1: "discharge_oc",
                2: "charge_oc",
                4: "ambient_high_temp",
                5: "ambient_low_temp",
            },
        )
        offset += 1

        # Byte 14: Number of Temperature Probes
        temp_probe_count = data[offset]
        offset += 1

        # Parse temperature data (N bytes, each = actual temp + 40°C offset)
        temperatures = []
        for i in range(temp_probe_count):
            if offset < len(data):
                temp_raw = data[offset]
                temp = parse_temperature(temp_raw)
                temperatures.append(temp)
                offset += 1

        # Parse remaining fields (variable position due to temperature data)
        software_version = data[offset] if offset < len(data) else 0
        offset += 1

        mos_state_raw = data[offset] if offset < len(data) else 0
        mos_state = extract_bitfield_flags(
            mos_state_raw, {1: "discharge_mos_on", 2: "charge_mos_on"}
        )
        offset += 1

        failure_status_raw = data[offset] if offset < len(data) else 0
        failure_status = extract_bitfield_flags(
            failure_status_raw,
            {
                0: "temp_acquisition_fail",
                1: "voltage_acquisition_fail",
                2: "discharge_mos_fail",
                3: "charge_mos_fail",
            },
        )

        logger.debug(
            "Parsed current status response: current=%.2fA, %d temp probes",
            current,
            temp_probe_count,
        )

        return cls(
            status_flags=status_flags,
            current=current,
            overvoltage_protection=ov_protection,
            undervoltage_protection=uv_protection,
            temperature_protection=temp_protection,
            general_protection=general_protection,
            temp_probe_count=temp_probe_count,
            temperatures=temperatures,
            software_version=software_version,
            mos_state=mos_state,
            failure_status=failure_status,
        )


# Register command
COMMANDS[CommandId.CURRENT_STATUS_REQUEST] = CommandSpec(
    req=CurrentStatusRequest, resp=CurrentStatusResponse
)

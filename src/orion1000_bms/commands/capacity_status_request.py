"""Capacity and status request command implementation."""

from __future__ import annotations
import logging
import struct
from dataclasses import dataclass
from .registry import CommandId, COMMANDS
from .base import CommandSpec

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
class CapacityStatusResponse:
    """Response containing capacity and status information."""

    soc: int  # State of charge (%)
    design_capacity: float  # Design capacity in Ah
    full_capacity: float  # Full capacity in Ah
    remaining_capacity: float  # Remaining capacity in Ah
    cycle_count: int  # Cycle count
    charge_time: int  # Charge time in minutes
    discharge_time: int  # Discharge time in minutes
    max_voltage: float  # Max voltage in volts
    min_voltage: float  # Min voltage in volts
    hardware_version: int  # Hardware version
    scheme_id: int  # Configuration scheme ID
    reserved: bytes  # Reserved bytes

    @classmethod
    def from_payload(cls, payload: bytes) -> CapacityStatusResponse:
        """Parse capacity and status data from payload bytes.

        Args:
            payload: 23-byte payload (2 cmd bytes + 20 data bytes)

        Returns:
            CapacityStatusResponse with parsed data
        """
        if len(payload) != 23:
            logger.warning(
                "Invalid payload length for capacity status response: %d", len(payload)
            )
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # Parse fields according to spec
        soc = data[0]
        design_capacity_raw = struct.unpack(">H", data[1:3])[0]
        design_capacity = design_capacity_raw / 10.0  # Convert decahours to Ah

        full_capacity_raw = struct.unpack(">H", data[3:5])[0]
        full_capacity = full_capacity_raw / 10.0  # Convert decahours to Ah

        remaining_capacity_raw = struct.unpack(">H", data[5:7])[0]
        remaining_capacity = remaining_capacity_raw / 10.0  # Convert decahours to Ah

        cycle_count = struct.unpack(">H", data[7:9])[0]
        charge_time = struct.unpack(">H", data[9:11])[0]  # minutes
        discharge_time = struct.unpack(">H", data[11:13])[0]  # minutes

        max_voltage_raw = struct.unpack(">H", data[13:15])[0]
        max_voltage = max_voltage_raw / 1000.0  # Convert mV to V

        min_voltage_raw = struct.unpack(">H", data[15:17])[0]
        min_voltage = min_voltage_raw / 1000.0  # Convert mV to V

        hardware_version = data[17]
        scheme_id = data[18]
        reserved = data[19:21]  # 2 reserved bytes

        logger.debug(
            "Parsed capacity status response: SOC=%d%%, remaining=%.1fAh",
            soc,
            remaining_capacity,
        )

        return cls(
            soc=soc,
            design_capacity=design_capacity,
            full_capacity=full_capacity,
            remaining_capacity=remaining_capacity,
            cycle_count=cycle_count,
            charge_time=charge_time,
            discharge_time=discharge_time,
            max_voltage=max_voltage,
            min_voltage=min_voltage,
            hardware_version=hardware_version,
            scheme_id=scheme_id,
            reserved=reserved,
        )


# Register command
COMMANDS[CommandId.CAPACITY_STATUS_REQUEST] = CommandSpec(
    req=CapacityStatusRequest, resp=CapacityStatusResponse
)

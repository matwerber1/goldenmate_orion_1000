"""Command definitions for BMS operations."""

# Import all command implementations to register them
from . import voltage_request
from . import current_status_request
from . import capacity_status_request
from . import serial_number_request
from . import mos_control

# Re-export commonly used classes
from .voltage_request import VoltageRequest, VoltageResponse
from .current_status_request import CurrentStatusRequest, CurrentStatusResponse
from .capacity_status_request import CapacityStatusRequest, CapacityStatusResponse
from .serial_number_request import SerialNumberRequest, SerialNumberResponse
from .mos_control import (
    AllowDischargeRequest,
    DisallowDischargeRequest,
    AllowChargeRequest,
    DisallowChargeRequest,
    MosControlResponse,
)
from .registry import CommandId, COMMANDS
from .base import CommandSpec

__all__ = [
    "VoltageRequest",
    "VoltageResponse",
    "CapacityStatusRequest",
    "CapacityStatusResponse",
    "CurrentStatusRequest",
    "CurrentStatusResponse",
    "SerialNumberRequest",
    "SerialNumberResponse",
    "AllowDischargeRequest",
    "DisallowDischargeRequest",
    "AllowChargeRequest",
    "DisallowChargeRequest",
    "MosControlResponse",
]

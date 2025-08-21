"""MOS control commands implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from .registry import CommandId, COMMANDS
from .base import CommandSpec, ResponseBase

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AllowDischargeRequest:
    """Request to allow discharge (open discharge MOS)."""

    command_id: int = CommandId.ALLOW_DISCHARGE
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for MOS control)."""
        return b""


@dataclass(slots=True)
class DisallowDischargeRequest:
    """Request to disallow discharge (close discharge MOS)."""

    command_id: int = CommandId.DISALLOW_DISCHARGE
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for MOS control)."""
        return b""


@dataclass(slots=True)
class AllowChargeRequest:
    """Request to allow charge."""

    command_id: int = CommandId.ALLOW_CHARGE
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for MOS control)."""
        return b""


@dataclass(slots=True)
class DisallowChargeRequest:
    """Request to disallow charge."""

    command_id: int = CommandId.DISALLOW_CHARGE
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for MOS control)."""
        return b""


@dataclass(slots=True, frozen=True)
class MosControlResponse(ResponseBase):
    """Response from MOS control commands."""

    command_id: int  # Echo of the command
    status: int  # Status byte (0x00 = success, other = failure)

    @classmethod
    def from_payload(cls, payload: bytes) -> MosControlResponse:
        """Parse MOS control response from payload bytes.

        Args:
            payload: Payload with command bytes + 1 status byte

        Returns:
            MosControlResponse with command echo and status
        """
        # Validate expected data length: 1 status byte
        cls.validate_payload_length(payload, 1)

        # Command bytes are echoed back
        cmd_hi = payload[0]
        cmd_lo = payload[1]
        command_id = cmd_lo  # Use command low byte as ID

        # Status byte
        status = payload[2]

        logger.debug(
            "Parsed MOS control response: cmd=0x%02x, status=0x%02x", command_id, status
        )

        return cls(command_id=command_id, status=status)

    @property
    def success(self) -> bool:
        """Check if the command was successful."""
        return self.status == 0x00


# Register commands
COMMANDS[CommandId.ALLOW_DISCHARGE] = CommandSpec(
    req=AllowDischargeRequest, resp=MosControlResponse
)

COMMANDS[CommandId.DISALLOW_DISCHARGE] = CommandSpec(
    req=DisallowDischargeRequest, resp=MosControlResponse
)

COMMANDS[CommandId.ALLOW_CHARGE] = CommandSpec(
    req=AllowChargeRequest, resp=MosControlResponse
)

COMMANDS[CommandId.DISALLOW_CHARGE] = CommandSpec(
    req=DisallowChargeRequest, resp=MosControlResponse
)

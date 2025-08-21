"""Read current command implementation."""

from __future__ import annotations
from dataclasses import dataclass
import struct
from .registry import CommandId, COMMANDS
from .base import CommandSpec


@dataclass(slots=True)
class ReadCurrentRequest:
    """Request to read pack current."""

    command_id: int = CommandId.READ_CURRENT
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for read commands)."""
        return b""


@dataclass(slots=True, frozen=True)
class ReadCurrentResponse:
    """Response containing pack current."""

    current: float  # Current in amperes

    @classmethod
    def from_payload(cls, payload: bytes) -> ReadCurrentResponse:
        """Parse current from payload bytes.

        Args:
            payload: 2-byte payload containing current in 0.1A units

        Returns:
            ReadCurrentResponse with current in amperes
        """
        if len(payload) != 2:
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Current is big-endian 16-bit unsigned integer in 0.1A units
        current_raw = struct.unpack(">H", payload)[0]
        current = current_raw / 10.0

        return cls(current=current)


# Register command
COMMANDS[CommandId.READ_CURRENT] = CommandSpec(
    req=ReadCurrentRequest, resp=ReadCurrentResponse
)

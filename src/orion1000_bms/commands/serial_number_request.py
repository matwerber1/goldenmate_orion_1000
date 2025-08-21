"""Serial number request command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from .registry import CommandId, COMMANDS
from .base import CommandSpec

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SerialNumberRequest:
    """Request to read device serial number."""

    command_id: int = CommandId.SERIAL_NUMBER_REQUEST
    address: int = 0x01

    def to_payload(self) -> bytes:
        """Convert to payload bytes (empty for serial number request)."""
        return b""


@dataclass(slots=True, frozen=True)
class SerialNumberResponse:
    """Response containing device serial number."""

    serial_number: str  # ASCII serial number string

    @classmethod
    def from_payload(cls, payload: bytes) -> SerialNumberResponse:
        """Parse serial number from payload bytes.

        Args:
            payload: Variable length payload (2 cmd bytes + 1 length byte + ASCII data)

        Returns:
            SerialNumberResponse with parsed serial number
        """
        if len(payload) < 3:
            logger.warning(
                "Invalid payload length for serial number response: %d", len(payload)
            )
            raise ValueError(f"Invalid payload length: {len(payload)}")

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # First byte is length of ASCII string
        length = data[0]

        if len(data) < 1 + length:
            logger.warning(
                "Insufficient data for serial number: expected %d, got %d",
                1 + length,
                len(data),
            )
            raise ValueError(f"Insufficient data for serial number")

        # Extract ASCII string
        serial_bytes = data[1 : 1 + length]
        serial_number = serial_bytes.decode("ascii", errors="replace")

        logger.debug("Parsed serial number: %s", serial_number)

        return cls(serial_number=serial_number)


# Register command
COMMANDS[CommandId.SERIAL_NUMBER_REQUEST] = CommandSpec(
    req=SerialNumberRequest, resp=SerialNumberResponse
)

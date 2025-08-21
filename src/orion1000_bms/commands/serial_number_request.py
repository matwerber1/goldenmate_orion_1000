"""Serial number request command implementation."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from .registry import CommandId, COMMANDS
from .base import CommandSpec, ResponseBase

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
class SerialNumberResponse(ResponseBase):
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
            raise ValueError(f"Payload too short for serial number: {len(payload)}")

        # Skip command bytes (first 2 bytes)
        data = payload[2:]

        # First byte is length of ASCII string
        length = data[0]

        # Validate we have enough data for the specified length
        expected_data_bytes = 1 + length  # length byte + ASCII data
        if len(data) < expected_data_bytes:
            raise ValueError(
                f"Insufficient data for serial number: expected {expected_data_bytes}, got {len(data)}"
            )

        # Extract ASCII string
        serial_bytes = data[1 : 1 + length]
        serial_number = serial_bytes.decode("ascii", errors="replace")

        logger.debug("Parsed serial number: %s", serial_number)

        return cls(serial_number=serial_number)


# Register command
COMMANDS[CommandId.SERIAL_NUMBER_REQUEST] = CommandSpec(
    req=SerialNumberRequest, resp=SerialNumberResponse
)

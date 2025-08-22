"""Base command and response protocols."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Protocol, Type, Dict, Any, Optional, cast
import logging
from enum import IntEnum
import time


class BaseCommand(Protocol):
    """Protocol for BMS command requests."""

    command_id: int
    address: int

    def to_payload(self) -> bytes:
        """Convert command to payload bytes."""
        ...


@dataclass(slots=True, frozen=True)
class ResponseMetadata:
    """Metadata for BMS responses."""

    tcp_host: str
    tcp_port: int
    request_timestamp: float
    response_timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "tcp_host": self.tcp_host,
            "tcp_port": self.tcp_port,
            "request_timestamp": self.request_timestamp,
            "response_timestamp": self.response_timestamp,
            "response_time_ms": round(
                (self.response_timestamp - self.request_timestamp) * 1000, 2
            ),
        }


class ResponseBase:
    """Base class for BMS command responses with validation and JSON serialization."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Note: Dataclass validation happens at runtime when the decorator is applied

    def set_metadata(self, metadata: ResponseMetadata) -> None:
        """Set response metadata (called by client)."""
        object.__setattr__(self, "_metadata", metadata)

    @property
    def metadata(self) -> Optional[ResponseMetadata]:
        """Get response metadata."""
        return getattr(self, "_metadata", None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to JSON-serializable dictionary."""
        # Use asdict if this is a dataclass, otherwise create dict manually
        if hasattr(self, "__dataclass_fields__"):
            # Cast to Any to avoid mypy issues with asdict
            result = asdict(cast(Any, self))
        else:
            # Fallback for non-dataclass responses
            result = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        # Add metadata if available
        if self.metadata:
            result["_metadata"] = self.metadata.to_dict()

        # Convert bytes fields to hex strings for JSON serialization
        def convert_bytes(obj: Any) -> Any:
            if isinstance(obj, bytes):
                return obj.hex()
            elif isinstance(obj, dict):
                return {k: convert_bytes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_bytes(item) for item in obj]
            return obj

        return convert_bytes(result)

    @classmethod
    def validate_payload_length(cls, payload: bytes, expected_data_bytes: int) -> None:
        """Validate payload has expected length based on protocol.

        Args:
            payload: Complete payload including command bytes
            expected_data_bytes: Expected number of data bytes (excluding command bytes)
        """
        expected_total = 2 + expected_data_bytes  # cmd_hi + cmd_lo + data
        if len(payload) != expected_total:
            raise ValueError(
                f"Invalid payload length: {len(payload)}, expected {expected_total}"
            )

    @classmethod
    def validate_minimum_payload_length(
        cls, payload: bytes, min_data_bytes: int
    ) -> None:
        """Validate payload has minimum required length for variable-length responses.

        Args:
            payload: Complete payload including command bytes
            min_data_bytes: Minimum number of data bytes required
        """
        min_total = 2 + min_data_bytes  # cmd_hi + cmd_lo + min_data
        if len(payload) < min_total:
            raise ValueError(
                f"Payload too short: {len(payload)}, minimum required {min_total}"
            )


class BaseResponse(Protocol):
    """Protocol for BMS command responses."""

    @classmethod
    def from_payload(cls, payload: bytes) -> "BaseResponse":
        """Parse response from payload bytes.

        Args:
            payload: Complete payload including command bytes and data
        """
        ...


@dataclass(slots=True, frozen=True)
class CommandSpec:
    """Command specification mapping request/response types."""

    req: Type[BaseCommand]
    resp: Type[BaseResponse]

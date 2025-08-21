"""Base command and response protocols."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Type
import logging
from enum import IntEnum


class BaseCommand(Protocol):
    """Protocol for BMS command requests."""

    command_id: int
    address: int

    def to_payload(self) -> bytes:
        """Convert command to payload bytes."""
        ...


class ResponseBase:
    """Base class for BMS command responses with validation."""

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

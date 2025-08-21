"""Base command and response protocols."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Type
from enum import IntEnum


class BaseCommand(Protocol):
    """Protocol for BMS command requests."""
    
    command_id: int
    address: int
    
    def to_payload(self) -> bytes:
        """Convert command to payload bytes."""
        ...


class BaseResponse(Protocol):
    """Protocol for BMS command responses."""
    
    @classmethod
    def from_payload(cls, payload: bytes) -> "BaseResponse":
        """Parse response from payload bytes."""
        ...


@dataclass(slots=True, frozen=True)
class CommandSpec:
    """Command specification mapping request/response types."""
    req: Type[BaseCommand]
    resp: Type[BaseResponse]
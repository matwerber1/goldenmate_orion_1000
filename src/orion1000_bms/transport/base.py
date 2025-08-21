"""Abstract transport interface."""

from abc import ABC, abstractmethod
from typing import Protocol


class AbstractTransport(Protocol):
    """Abstract transport protocol for BMS communication."""
    
    @abstractmethod
    def open_if_needed(self) -> None:
        """Open connection if not already open."""
        ...
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        ...
    
    @abstractmethod
    def send_request(self, payload: bytes, *, timeout: float | None = None) -> bytes:
        """Send request and return response bytes.
        
        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout in seconds
            
        Returns:
            Response frame bytes
        """
        ...
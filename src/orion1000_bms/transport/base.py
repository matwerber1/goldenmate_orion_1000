"""Abstract transport interface."""

import time
from abc import ABC, abstractmethod
from typing import Protocol
from ..exceptions import TimeoutError
from ..logging import get_logger


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


class BaseTransport(ABC):
    """Base transport with retry logic."""

    def __init__(self, *, max_retries: int = 3) -> None:
        """Initialize base transport.

        Args:
            max_retries: Maximum number of retries on timeout (default: 3)
        """
        self.max_retries = max_retries
        self._logger = get_logger(__name__)

    @abstractmethod
    def _send_request_impl(
        self, payload: bytes, *, timeout: float | None = None
    ) -> bytes:
        """Implementation-specific request sending.

        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout in seconds

        Returns:
            Response frame bytes
        """
        ...

    def send_request(self, payload: bytes, *, timeout: float | None = None) -> bytes:
        """Send request with automatic retries on timeout.

        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout in seconds

        Returns:
            Response frame bytes
        """
        last_error: TimeoutError | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._send_request_impl(payload, timeout=timeout)
            except TimeoutError as e:
                last_error = e
                if attempt < self.max_retries:
                    self._logger.debug(
                        "Request timeout, retrying (%d/%d)",
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(0.1)  # Brief delay before retry
                else:
                    self._logger.debug(
                        "Request failed after %d retries", self.max_retries
                    )

        assert last_error is not None
        raise last_error

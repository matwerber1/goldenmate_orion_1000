"""Test retry functionality in transport layer."""

import pytest
from unittest.mock import Mock, patch
from orion1000_bms.transport.base import BaseTransport
from orion1000_bms.exceptions import TimeoutError, TransportError


class MockTransport(BaseTransport):
    """Mock transport for testing retry logic."""

    def __init__(self, *, max_retries: int = 3) -> None:
        super().__init__(max_retries=max_retries)
        self.call_count = 0
        self.should_timeout = True

    def open_if_needed(self) -> None:
        pass

    def close(self) -> None:
        pass

    def _send_request_impl(
        self, payload: bytes, *, timeout: float | None = None
    ) -> bytes:
        self.call_count += 1
        if self.should_timeout:
            raise TimeoutError("Mock timeout")
        return b"response"


def test_retry_on_timeout() -> None:
    """Test that requests are retried on timeout."""
    transport = MockTransport(max_retries=2)

    with pytest.raises(TimeoutError):
        transport.send_request(b"test")

    # Should have tried 3 times (initial + 2 retries)
    assert transport.call_count == 3


def test_success_after_retry() -> None:
    """Test that request succeeds after initial timeout."""
    transport = MockTransport(max_retries=2)

    # Fail first call, succeed on second
    def mock_impl(payload: bytes, *, timeout: float | None = None) -> bytes:
        transport.call_count += 1
        if transport.call_count == 1:
            raise TimeoutError("Mock timeout")
        return b"response"

    with patch.object(transport, "_send_request_impl", side_effect=mock_impl):
        result = transport.send_request(b"test")
        assert result == b"response"
        assert transport.call_count == 2


def test_non_timeout_error_not_retried() -> None:
    """Test that non-timeout errors are not retried."""
    transport = MockTransport(max_retries=2)

    def mock_impl(payload: bytes, *, timeout: float | None = None) -> bytes:
        transport.call_count += 1
        raise TransportError("Mock transport error")

    with patch.object(transport, "_send_request_impl", side_effect=mock_impl):
        with pytest.raises(TransportError):
            transport.send_request(b"test")

        # Should only try once
        assert transport.call_count == 1


def test_configurable_max_retries() -> None:
    """Test that max_retries is configurable."""
    transport = MockTransport(max_retries=1)

    with pytest.raises(TimeoutError):
        transport.send_request(b"test")

    # Should have tried 2 times (initial + 1 retry)
    assert transport.call_count == 2

"""Unit tests for exception hierarchy."""

import pytest
from orion1000_bms.exceptions import (
    BmsError, TransportError, TimeoutError, ChecksumError,
    FrameError, ProtocolError, UnsupportedCommandError
)


@pytest.mark.phase4
def test_exception_hierarchy() -> None:
    """Test exception inheritance hierarchy."""
    # All exceptions inherit from BmsError
    assert issubclass(TransportError, BmsError)
    assert issubclass(ChecksumError, BmsError)
    assert issubclass(FrameError, BmsError)
    assert issubclass(ProtocolError, BmsError)
    assert issubclass(UnsupportedCommandError, BmsError)
    
    # TimeoutError inherits from TransportError
    assert issubclass(TimeoutError, TransportError)
    assert issubclass(TimeoutError, BmsError)


@pytest.mark.phase4
def test_exception_instantiation() -> None:
    """Test exception can be instantiated with messages."""
    msg = "Test error message"
    
    exc = BmsError(msg)
    assert str(exc) == msg
    
    exc = TransportError(msg)
    assert str(exc) == msg
    
    exc = TimeoutError(msg)
    assert str(exc) == msg


@pytest.mark.phase4
def test_exception_catching() -> None:
    """Test exception catching works correctly."""
    # TimeoutError can be caught as TransportError or BmsError
    try:
        raise TimeoutError("timeout")
    except TransportError:
        pass  # Should catch
    else:
        pytest.fail("Should have caught TimeoutError as TransportError")
    
    try:
        raise ChecksumError("checksum")
    except BmsError:
        pass  # Should catch
    else:
        pytest.fail("Should have caught ChecksumError as BmsError")
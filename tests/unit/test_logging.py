"""Unit tests for logging utilities."""

import logging
import pytest
from orion1000_bms.logging import get_logger, hex_dump, log_frame_tx, log_frame_rx


@pytest.mark.phase4
def test_get_logger() -> None:
    """Test logger factory."""
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"

    # Should have NullHandler by default
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.NullHandler)


@pytest.mark.phase4
def test_get_logger_no_duplicate_handlers() -> None:
    """Test logger doesn't add duplicate handlers."""
    logger1 = get_logger("test.same")
    logger2 = get_logger("test.same")

    # Should be same logger instance
    assert logger1 is logger2
    # Should still have only one handler
    assert len(logger1.handlers) == 1


@pytest.mark.phase4
def test_hex_dump_empty() -> None:
    """Test hex dump with empty data."""
    result = hex_dump(b"")
    assert result == "<empty>"

    result = hex_dump(b"", "PREFIX: ")
    assert result == "PREFIX: <empty>"


@pytest.mark.phase4
def test_hex_dump_single_byte() -> None:
    """Test hex dump with single byte."""
    result = hex_dump(b"\xea")
    assert result == "EA"

    result = hex_dump(b"\xea", "TX: ")
    assert result == "TX: EA"


@pytest.mark.phase4
def test_hex_dump_multiple_bytes() -> None:
    """Test hex dump with multiple bytes."""
    data = b"\xea\xd1\x01\x02\x03\x00\xd1\xf5"
    result = hex_dump(data)
    assert result == "EA D1 01 02 03 00 D1 F5"

    result = hex_dump(data, "FRAME: ")
    assert result == "FRAME: EA D1 01 02 03 00 D1 F5"


@pytest.mark.phase4
def test_log_frame_functions() -> None:
    """Test frame logging functions."""
    logger = get_logger("test.frames")
    frame = b"\xea\xd1\x01\x02\x03\x00\xd1\xf5"

    # These should not raise exceptions
    log_frame_tx(logger, frame)
    log_frame_rx(logger, frame)
    log_frame_tx(logger, frame, "SEND")
    log_frame_rx(logger, frame, "RECV")

    # Test with empty frame
    log_frame_tx(logger, b"")
    log_frame_rx(logger, b"")

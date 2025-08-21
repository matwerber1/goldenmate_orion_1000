"""Integration tests using golden frame fixtures."""

import pytest
from orion1000_bms.protocol.codec import decode
from orion1000_bms.commands.read_total_voltage import ReadTotalVoltageResponse
from orion1000_bms.commands.read_current import ReadCurrentResponse
from orion1000_bms.commands.read_cell_voltage import ReadCellVoltageResponse
from .data.frames.golden_frames import GOLDEN_FRAMES


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    return bytes.fromhex(hex_str.replace(" ", ""))


@pytest.mark.phase5
def test_golden_read_total_voltage() -> None:
    """Test read total voltage golden frame."""
    request_hex, response_hex = GOLDEN_FRAMES["read_total_voltage"]

    # Decode response frame
    response_bytes = hex_to_bytes(response_hex)
    frame = decode(response_bytes)

    # Verify frame structure
    assert frame.cmd_hi == 0x03
    assert frame.cmd_lo == 0x00
    assert len(frame.payload) == 2

    # Parse response payload
    resp = ReadTotalVoltageResponse.from_payload(frame.payload)
    assert resp.voltage == 48.5


@pytest.mark.phase5
def test_golden_read_current() -> None:
    """Test read current golden frame."""
    request_hex, response_hex = GOLDEN_FRAMES["read_current"]

    # Decode response frame
    response_bytes = hex_to_bytes(response_hex)
    frame = decode(response_bytes)

    # Verify frame structure
    assert frame.cmd_hi == 0x03
    assert frame.cmd_lo == 0x02
    assert len(frame.payload) == 2

    # Parse response payload
    resp = ReadCurrentResponse.from_payload(frame.payload)
    assert resp.current == 10.5


@pytest.mark.phase5
def test_golden_read_cell_voltage() -> None:
    """Test read cell voltage golden frame."""
    request_hex, response_hex = GOLDEN_FRAMES["read_cell_voltage_0"]

    # Decode response frame
    response_bytes = hex_to_bytes(response_hex)
    frame = decode(response_bytes)

    # Verify frame structure
    assert frame.cmd_hi == 0x03
    assert frame.cmd_lo == 0x01
    assert len(frame.payload) == 3

    # Parse response payload
    resp = ReadCellVoltageResponse.from_payload(frame.payload)
    assert resp.cell_index == 0
    assert resp.voltage == 3.456


@pytest.mark.phase5
def test_golden_request_frames() -> None:
    """Test golden request frames can be decoded."""
    for name, (request_hex, response_hex) in GOLDEN_FRAMES.items():
        request_bytes = hex_to_bytes(request_hex)
        frame = decode(request_bytes)

        # All requests should have valid frame structure
        assert frame.start == 0xEA
        assert frame.product_id == 0xD1
        assert frame.address == 0x01
        assert frame.end == 0xF5

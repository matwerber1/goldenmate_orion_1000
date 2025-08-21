"""Integration tests using golden frame fixtures."""

import pytest
from orion1000_bms.protocol.codec import decode
from orion1000_bms.commands import VoltageResponse, CurrentStatusResponse
from .data.frames.golden_frames import GOLDEN_FRAMES


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    return bytes.fromhex(hex_str.replace(" ", ""))


@pytest.mark.phase5
def test_golden_voltage_request() -> None:
    """Test voltage request golden frame."""
    request_hex, response_hex = GOLDEN_FRAMES["voltage_request"]

    # Decode response frame
    response_bytes = hex_to_bytes(response_hex)
    frame = decode(response_bytes)

    # Verify frame structure
    assert frame.cmd_hi == 0xFF
    assert frame.cmd_lo == 0x02
    assert len(frame.payload) == 39  # 32 cell voltages + 6 temperatures + 1 string count

    # Parse response payload (include command bytes)
    full_payload = bytes([frame.cmd_hi, frame.cmd_lo]) + frame.payload
    resp = VoltageResponse.from_payload(full_payload)
    assert len(resp.cell_voltages) == 16
    assert len(resp.temperatures) == 3
    assert resp.system_string_count == 2


@pytest.mark.phase5
def test_golden_current_status_request() -> None:
    """Test current status request golden frame."""
    request_hex, response_hex = GOLDEN_FRAMES["current_status_request"]

    # Decode response frame
    response_bytes = hex_to_bytes(response_hex)
    frame = decode(response_bytes)

    # Verify frame structure
    assert frame.cmd_hi == 0xFF
    assert frame.cmd_lo == 0x03
    assert len(frame.payload) == 13  # Status data payload (without command bytes)

    # Parse response payload (include command bytes)
    full_payload = bytes([frame.cmd_hi, frame.cmd_lo]) + frame.payload
    resp = CurrentStatusResponse.from_payload(full_payload)
    assert resp.current == 10.5
    assert len(resp.temperatures) == 3


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
        assert frame.cmd_hi == 0xFF  # Command High always 0xFF
        assert frame.end == 0xF5

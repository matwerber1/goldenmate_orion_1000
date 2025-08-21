"""Unit tests for codec functions."""

import pytest
from orion1000_bms.protocol.codec import build_frame, decode, xor_checksum
from orion1000_bms.protocol.constants import PRODUCT_ID_DEFAULT


def test_build_frame_minimal() -> None:
    """Test building minimal frame with no payload."""
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    expected = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    assert raw == expected


def test_build_frame_with_payload() -> None:
    """Test building frame with payload."""
    payload = b"\x12\x34"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, payload)
    
    # Verify structure
    assert raw[0] == 0xEA  # start
    assert raw[1] == PRODUCT_ID_DEFAULT  # product_id
    assert raw[2] == 0x01  # address
    assert raw[3] == 0x04  # data_len (2 cmd + 2 payload)
    assert raw[4] == 0x03  # cmd_hi
    assert raw[5] == 0x00  # cmd_lo
    assert raw[6:8] == payload  # payload
    assert raw[-1] == 0xF5  # end
    
    # Verify checksum
    checksum_data = raw[1:-2]  # product_id through payload
    expected_checksum = xor_checksum(checksum_data)
    assert raw[-2] == expected_checksum


def test_decode_round_trip() -> None:
    """Test decode matches build_frame output."""
    payload = b"\xAB\xCD\xEF"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x05, 0x12, 0x34, payload)
    frame = decode(raw)
    
    assert frame.product_id == PRODUCT_ID_DEFAULT
    assert frame.address == 0x05
    assert frame.cmd_hi == 0x12
    assert frame.cmd_lo == 0x34
    assert frame.payload == payload


def test_build_frame_different_product_id() -> None:
    """Test building frame with different product ID."""
    raw = build_frame(0xAA, 0x02, 0x05, 0x06, b"\xFF")
    frame = decode(raw)
    
    assert frame.product_id == 0xAA
    assert frame.address == 0x02
    assert frame.cmd_hi == 0x05
    assert frame.cmd_lo == 0x06
    assert frame.payload == b"\xFF"


def test_build_frame_max_values() -> None:
    """Test building frame with maximum byte values."""
    raw = build_frame(0xFF, 0xFF, 0xFF, 0xFF, b"\xFF\xFF")
    frame = decode(raw)
    
    assert frame.product_id == 0xFF
    assert frame.address == 0xFF
    assert frame.cmd_hi == 0xFF
    assert frame.cmd_lo == 0xFF
    assert frame.payload == b"\xFF\xFF"
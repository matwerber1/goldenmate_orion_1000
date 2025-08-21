"""Unit tests for frame encoding/decoding."""

import pytest
from orion1000_bms.protocol.frame import Frame
from orion1000_bms.protocol.codec import build_frame, decode
from orion1000_bms.protocol.constants import START, END, PRODUCT_ID_DEFAULT


def test_frame_round_trip():
    """Test frame encode/decode round trip."""
    frame = Frame(
        start=START,
        product_id=PRODUCT_ID_DEFAULT,
        address=0x01,
        data_len=0x02,
        cmd_hi=0x03,
        cmd_lo=0x00,
        payload=b"",
        checksum=0xD1,
        end=END
    )
    
    # Encode to bytes
    raw = frame.to_bytes()
    
    # Decode back to frame
    decoded = Frame.from_bytes(raw)
    
    assert decoded == frame


def test_build_frame():
    """Test build_frame function."""
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    expected = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    assert raw == expected


def test_decode_function():
    """Test decode function."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    frame = decode(raw)
    
    assert frame.start == START
    assert frame.product_id == PRODUCT_ID_DEFAULT
    assert frame.address == 0x01
    assert frame.data_len == 0x02
    assert frame.cmd_hi == 0x03
    assert frame.cmd_lo == 0x00
    assert frame.payload == b""
    assert frame.checksum == 0xD1
    assert frame.end == END


def test_frame_with_payload():
    """Test frame with payload data."""
    payload = b"\x12\x34"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, payload)
    frame = decode(raw)
    
    assert frame.payload == payload
    assert frame.data_len == 4  # 2 cmd bytes + 2 payload bytes


def test_invalid_start_byte():
    """Test frame with invalid start byte."""
    raw = b"\xFF\xD1\x01\x02\x03\x00\xD1\xF5"
    with pytest.raises(ValueError, match="Invalid start byte"):
        Frame.from_bytes(raw)


def test_invalid_end_byte():
    """Test frame with invalid end byte."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xFF"
    with pytest.raises(ValueError, match="Invalid end byte"):
        Frame.from_bytes(raw)


def test_invalid_checksum():
    """Test frame with invalid checksum."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xFF\xF5"
    with pytest.raises(ValueError, match="Checksum mismatch"):
        Frame.from_bytes(raw)


def test_frame_too_short():
    """Test frame that is too short."""
    raw = b"\xEA\xD1\x01"
    with pytest.raises(ValueError, match="Frame too short"):
        Frame.from_bytes(raw)


def test_invalid_frame_length():
    """Test frame with incorrect length."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5\xFF"  # Extra byte
    with pytest.raises(ValueError, match="Invalid frame length"):
        Frame.from_bytes(raw)


def test_frame_minimum_length():
    """Test frame at minimum valid length."""
    # Minimum frame: start + product_id + address + data_len(2) + cmd_hi + cmd_lo + checksum + end = 8 bytes
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    frame = Frame.from_bytes(raw)
    assert frame.data_len == 2
    assert frame.payload == b""


def test_frame_large_payload():
    """Test frame with larger payload."""
    payload = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, payload)
    frame = decode(raw)
    assert frame.payload == payload
    assert frame.data_len == 10  # 2 cmd bytes + 8 payload bytes
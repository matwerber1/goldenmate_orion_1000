"""Unit tests for frame encoding/decoding."""

import pytest
from orion1000_bms.protocol.frame import Frame
from orion1000_bms.protocol.codec import build_frame, decode
from orion1000_bms.protocol.constants import START, END, PRODUCT_ID_DEFAULT
from orion1000_bms.exceptions import FrameError, ChecksumError


@pytest.mark.phase2
def test_frame_round_trip() -> None:
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


@pytest.mark.phase2
def test_build_frame() -> None:
    """Test build_frame function."""
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    expected = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    assert raw == expected


@pytest.mark.phase2
def test_decode_function() -> None:
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


@pytest.mark.phase2
def test_frame_with_payload() -> None:
    """Test frame with payload data."""
    payload = b"\x12\x34"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, payload)
    frame = decode(raw)
    
    assert frame.payload == payload
    assert frame.data_len == 4  # 2 cmd bytes + 2 payload bytes


@pytest.mark.phase2
def test_invalid_start_byte() -> None:
    """Test frame with invalid start byte."""
    raw = b"\xFF\xD1\x01\x02\x03\x00\xD1\xF5"
    with pytest.raises(FrameError, match="Invalid start byte"):
        Frame.from_bytes(raw)


@pytest.mark.phase2
def test_invalid_end_byte() -> None:
    """Test frame with invalid end byte."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xFF"
    with pytest.raises(FrameError, match="Invalid end byte"):
        Frame.from_bytes(raw)


@pytest.mark.phase2
def test_invalid_checksum() -> None:
    """Test frame with invalid checksum."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xFF\xF5"
    with pytest.raises(ChecksumError, match="Checksum mismatch"):
        Frame.from_bytes(raw)


@pytest.mark.phase2
def test_frame_too_short() -> None:
    """Test frame that is too short."""
    raw = b"\xEA\xD1\x01"
    with pytest.raises(FrameError, match="Frame too short"):
        Frame.from_bytes(raw)


@pytest.mark.phase2
def test_invalid_frame_length() -> None:
    """Test frame with incorrect length."""
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5\xFF"  # Extra byte
    with pytest.raises(FrameError, match="Invalid frame length"):
        Frame.from_bytes(raw)


@pytest.mark.phase2
def test_frame_minimum_length() -> None:
    """Test frame at minimum valid length."""
    # Minimum frame: start + product_id + address + data_len(2) + cmd_hi + cmd_lo + checksum + end = 8 bytes
    raw = b"\xEA\xD1\x01\x02\x03\x00\xD1\xF5"
    frame = Frame.from_bytes(raw)
    assert frame.data_len == 2
    assert frame.payload == b""


@pytest.mark.phase2
def test_frame_large_payload() -> None:
    """Test frame with larger payload."""
    payload = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    raw = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, payload)
    frame = decode(raw)
    assert frame.payload == payload
    assert frame.data_len == 10  # 2 cmd bytes + 8 payload bytes
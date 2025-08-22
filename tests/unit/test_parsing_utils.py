"""Tests for parsing utilities."""

import pytest
from orion1000_bms.commands.parsing_utils import (
    parse_temperature,
    parse_big_endian_uint16,
    parse_big_endian_int16,
    extract_bitfield_flags,
    parse_tagged_data,
)


def test_parse_temperature() -> None:
    """Test temperature parsing with offset."""
    assert parse_temperature(40) == 0.0  # 40 - 40 = 0°C
    assert parse_temperature(65) == 25.0  # 65 - 40 = 25°C
    assert parse_temperature(15) == -25.0  # 15 - 40 = -25°C


def test_parse_big_endian_uint16() -> None:
    """Test big-endian unsigned 16-bit parsing."""
    data = b"\x12\x34\x56\x78"
    assert parse_big_endian_uint16(data, 0) == 0x1234
    assert parse_big_endian_uint16(data, 2) == 0x5678


def test_parse_big_endian_int16() -> None:
    """Test big-endian signed 16-bit parsing."""
    data = b"\x80\x00\x7f\xff"  # -32768, 32767
    assert parse_big_endian_int16(data, 0) == -32768
    assert parse_big_endian_int16(data, 2) == 32767


def test_extract_bitfield_flags() -> None:
    """Test bitfield flag extraction."""
    flag_map = {0: "flag0", 1: "flag1", 4: "flag4"}

    # Test with bits 0 and 4 set (0x11 = 0b00010001)
    result = extract_bitfield_flags(0x11, flag_map)
    assert result == {"flag0": True, "flag1": False, "flag4": True}

    # Test with no bits set
    result = extract_bitfield_flags(0x00, flag_map)
    assert result == {"flag0": False, "flag1": False, "flag4": False}


def test_parse_tagged_data() -> None:
    """Test tag-based data parsing."""
    # Create test data: tag1(1 byte), tag2(2 bytes), tag3(1 byte)
    data = b"\x01\x42\x02\x12\x34\x03\x99"

    tag_map = {
        0x01: ("field1", 1),
        0x02: ("field2", 2),
        0x03: ("field3", 1),
    }

    result = parse_tagged_data(data, tag_map)
    assert result == {
        "field1": 0x42,
        "field2": 0x1234,  # Big-endian 16-bit
        "field3": 0x99,
    }


def test_parse_tagged_data_unknown_tag() -> None:
    """Test tag-based parsing with unknown tags."""
    data = b"\x01\x42\xff\x99\x02\x12\x34"  # Unknown tag 0xFF

    tag_map = {
        0x01: ("field1", 1),
        0x02: ("field2", 2),
    }

    result = parse_tagged_data(data, tag_map)
    # Should skip unknown tag and continue parsing
    assert result == {
        "field1": 0x42,
        "field2": 0x1234,
    }

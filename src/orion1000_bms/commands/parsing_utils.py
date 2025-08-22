"""Common parsing utilities for BMS command responses."""

import struct
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_temperature(raw_value: int) -> float:
    """Convert raw temperature value to Celsius.

    Args:
        raw_value: Raw temperature value (actual temp + 40°C offset)

    Returns:
        Temperature in Celsius
    """
    return float(raw_value - 40)


def parse_big_endian_uint16(data: bytes, offset: int) -> int:
    """Parse big-endian unsigned 16-bit integer.

    Args:
        data: Byte array
        offset: Starting offset

    Returns:
        Parsed unsigned integer
    """
    return struct.unpack(">H", data[offset : offset + 2])[0]


def parse_big_endian_int16(data: bytes, offset: int) -> int:
    """Parse big-endian signed 16-bit integer.

    Args:
        data: Byte array
        offset: Starting offset

    Returns:
        Parsed signed integer
    """
    return struct.unpack(">h", data[offset : offset + 2])[0]


def extract_bitfield_flags(value: int, flag_map: Dict[int, str]) -> Dict[str, bool]:
    """Extract named flags from a bitfield value.

    Args:
        value: Bitfield value
        flag_map: Mapping of bit positions to flag names

    Returns:
        Dictionary of flag names to boolean values
    """
    return {name: bool(value & (1 << bit)) for bit, name in flag_map.items()}


def parse_tagged_data(
    data: bytes, tag_map: Dict[int, Tuple[str, int]]
) -> Dict[str, Any]:
    """Parse tag-based data structure.

    Args:
        data: Data bytes containing tagged fields
        tag_map: Mapping of tag values to (field_name, byte_count) tuples

    Returns:
        Dictionary of parsed field values
    """
    result = {}
    offset = 0

    while offset < len(data):
        if offset >= len(data):
            break

        tag = data[offset]
        offset += 1

        if tag in tag_map:
            field_name, byte_count = tag_map[tag]
            if offset + byte_count <= len(data):
                if byte_count == 1:
                    result[field_name] = data[offset]
                elif byte_count == 2:
                    result[field_name] = parse_big_endian_uint16(data, offset)
                else:
                    result[field_name] = data[offset : offset + byte_count]
                offset += byte_count
            else:
                logger.warning("Insufficient data for tag 0x%02x", tag)
                break
        else:
            logger.warning("Unknown tag 0x%02x at offset %d", tag, offset - 1)
            offset += 1

    return result

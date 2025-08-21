"""Unit tests for checksum calculation."""

import pytest
from orion1000_bms.protocol.codec import xor_checksum


def test_xor_checksum_empty():
    """Test checksum of empty data."""
    assert xor_checksum(b"") == 0


def test_xor_checksum_single_byte():
    """Test checksum of single byte."""
    assert xor_checksum(b"\xD1") == 0xD1


def test_xor_checksum_multiple_bytes():
    """Test checksum of multiple bytes."""
    # Example: ProductId(0xD1) + Address(0x01) + DataLen(0x02) + CmdHi(0x03) + CmdLo(0x00)
    data = b"\xD1\x01\x02\x03\x00"
    expected = 0xD1 ^ 0x01 ^ 0x02 ^ 0x03 ^ 0x00
    assert xor_checksum(data) == expected


def test_xor_checksum_spec_example():
    """Test checksum from protocol spec example."""
    # From spec: EA D1 01 02 03 00 D1 F5
    # Checksum covers: D1 01 02 03 00 = 0xD1
    data = b"\xD1\x01\x02\x03\x00"
    assert xor_checksum(data) == 0xD1
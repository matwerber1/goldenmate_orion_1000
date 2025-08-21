"""Unit tests for checksum calculation."""

import pytest
from orion1000_bms.protocol.codec import xor_checksum


@pytest.mark.phase1
def test_xor_checksum_empty() -> None:
    """Test checksum of empty data."""
    assert xor_checksum(b"") == 0


@pytest.mark.phase1
def test_xor_checksum_single_byte() -> None:
    """Test checksum of single byte."""
    assert xor_checksum(b"\xD1") == 0xD1


@pytest.mark.phase1
def test_xor_checksum_multiple_bytes() -> None:
    """Test checksum of multiple bytes."""
    # Example: DataLen(0x02) + CmdHi(0xFF) + CmdLo(0x02)
    data = b"\x02\xFF\x02"
    expected = 0x02 ^ 0xFF ^ 0x02
    assert xor_checksum(data) == expected


@pytest.mark.phase1
def test_xor_checksum_spec_example() -> None:
    """Test checksum from protocol spec example."""
    # From updated spec: EA D1 01 02 FF 02 FF F5
    # Checksum covers: Length(0x02) + CmdHi(0xFF) + CmdLo(0x02) = 0xFF
    data = b"\x02\xFF\x02"
    assert xor_checksum(data) == 0xFF
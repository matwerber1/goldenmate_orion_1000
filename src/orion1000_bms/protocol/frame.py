"""Frame dataclass for BMS protocol."""

from __future__ import annotations
from dataclasses import dataclass
from .constants import START, END, PRODUCT_ID_DEFAULT
from .codec import xor_checksum
from ..exceptions import FrameError, ChecksumError


@dataclass(slots=True, frozen=True)
class Frame:
    """BMS protocol frame structure."""
    start: int
    product_id: int
    address: int
    data_len: int
    cmd_hi: int
    cmd_lo: int
    payload: bytes
    checksum: int
    end: int

    def to_bytes(self) -> bytes:
        """Convert frame to bytes."""
        # Build frame without checksum first
        frame_data = bytes([
            self.start,
            self.product_id,
            self.address,
            self.data_len,
            self.cmd_hi,
            self.cmd_lo
        ]) + self.payload
        
        # Calculate checksum from product_id through payload
        checksum_data = frame_data[1:]  # Skip start byte
        calculated_checksum = xor_checksum(checksum_data)
        
        # Add checksum and end byte
        return frame_data + bytes([calculated_checksum, self.end])

    @classmethod
    def from_bytes(cls, raw: bytes) -> Frame:
        """Parse frame from bytes with validation."""
        if len(raw) < 8:
            raise FrameError("Frame too short")
        
        start = raw[0]
        if start != START:
            raise FrameError(f"Invalid start byte: {start:#x}")
        
        product_id = raw[1]
        address = raw[2]
        data_len = raw[3]
        
        # Validate frame length
        expected_len = 4 + data_len + 2  # header(4) + data_len + checksum + end
        if len(raw) != expected_len:
            raise FrameError(f"Invalid frame length: {len(raw)} != {expected_len}")
        
        cmd_hi = raw[4]
        cmd_lo = raw[5]
        payload = raw[6:4+data_len]  # data_len includes cmd bytes
        checksum = raw[4+data_len]
        end = raw[4+data_len+1]
        
        if end != END:
            raise FrameError(f"Invalid end byte: {end:#x}")
        
        # Verify checksum
        checksum_data = raw[1:4+data_len]  # product_id through payload
        expected_checksum = xor_checksum(checksum_data)
        if checksum != expected_checksum:
            raise ChecksumError(f"Checksum mismatch: {checksum:#x} != {expected_checksum:#x}")
        
        return cls(
            start=start,
            product_id=product_id,
            address=address,
            data_len=data_len,
            cmd_hi=cmd_hi,
            cmd_lo=cmd_lo,
            payload=payload,
            checksum=checksum,
            end=end
        )
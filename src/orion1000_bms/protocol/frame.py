"""Frame dataclass for BMS protocol."""

from __future__ import annotations
import logging
from dataclasses import dataclass
from .constants import START, END, PRODUCT_ID_DEFAULT
from .codec import xor_checksum
from ..exceptions import FrameError, ChecksumError

logger = logging.getLogger(__name__)


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
        frame_data = (
            bytes(
                [
                    self.start,
                    self.product_id,
                    self.address,
                    self.data_len,
                    self.cmd_hi,
                    self.cmd_lo,
                ]
            )
            + self.payload
        )

        # Calculate checksum from Length through payload (excluding Product ID and Address)
        checksum_data = frame_data[3:]  # Skip start, product_id, address
        calculated_checksum = xor_checksum(checksum_data)

        # Add checksum and end byte
        return frame_data + bytes([calculated_checksum, self.end])

    @classmethod
    def from_bytes(cls, raw: bytes) -> Frame:
        """Parse frame from bytes with validation."""
        if len(raw) < 8:
            logger.warning("Frame too short: %d bytes", len(raw))
            raise FrameError("Frame too short")

        start = raw[0]
        if start != START:
            logger.warning("Invalid start byte: 0x%02x", start)
            raise FrameError(f"Invalid start byte: {start:#x}")

        product_id = raw[1]
        address = raw[2]
        data_len = raw[3]

        # Validate frame length - data_len now includes checksum and end byte
        expected_len = (
            4 + data_len
        )  # header(4) + data_len (which includes everything after length)
        if len(raw) != expected_len:
            logger.warning("Invalid frame length: %d != %d", len(raw), expected_len)
            raise FrameError(f"Invalid frame length: {len(raw)} != {expected_len}")

        cmd_hi = raw[4]
        cmd_lo = raw[5]
        payload = raw[6 : 4 + data_len - 2]  # payload excludes checksum and end byte
        checksum = raw[4 + data_len - 2]  # checksum is 2nd to last byte
        end = raw[4 + data_len - 1]  # end is last byte

        if end != END:
            logger.warning("Invalid end byte: 0x%02x", end)
            raise FrameError(f"Invalid end byte: {end:#x}")

        # Verify checksum
        checksum_data = raw[
            3 : 4 + data_len - 2
        ]  # Length through payload (excluding checksum and end)
        expected_checksum = xor_checksum(checksum_data)
        if checksum != expected_checksum:
            logger.warning(
                "Checksum mismatch: 0x%02x != 0x%02x", checksum, expected_checksum
            )
            raise ChecksumError(
                f"Checksum mismatch: {checksum:#x} != {expected_checksum:#x}"
            )

        logger.debug(
            "Parsed frame: cmd=0x%02x%02x, addr=0x%02x", cmd_hi, cmd_lo, address
        )
        return cls(
            start=start,
            product_id=product_id,
            address=address,
            data_len=data_len,
            cmd_hi=cmd_hi,
            cmd_lo=cmd_lo,
            payload=payload,
            checksum=checksum,
            end=end,
        )

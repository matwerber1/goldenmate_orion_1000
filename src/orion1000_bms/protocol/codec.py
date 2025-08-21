"""Frame encoding/decoding and checksum functions."""

import logging
from .constants import START, END, PRODUCT_ID_DEFAULT
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .frame import Frame


def xor_checksum(data: bytes) -> int:
    """Calculate XOR checksum of data bytes.

    Args:
        data: Bytes to checksum (ProductId through Data)

    Returns:
        XOR checksum as integer
    """
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def build_frame(
    product_id: int, address: int, cmd_hi: int, cmd_lo: int, payload: bytes
) -> bytes:
    """Build a complete frame with checksum.

    Args:
        product_id: Product ID byte
        address: Device address
        cmd_hi: Command high byte
        cmd_lo: Command low byte
        payload: Command payload data

    Returns:
        Complete frame as bytes
    """
    data_len = 2 + len(payload)  # cmd bytes + payload

    # Build frame without checksum
    frame_data = bytes([START, product_id, address, data_len, cmd_hi, cmd_lo]) + payload

    # Calculate checksum from product_id through payload
    checksum_data = frame_data[1:]  # Skip start byte
    checksum = xor_checksum(checksum_data)

    # Add checksum and end
    frame = frame_data + bytes([checksum, END])
    logger.debug("Built frame: cmd=0x%02x%02x, len=%d", cmd_hi, cmd_lo, len(frame))
    return frame


def decode(raw: bytes) -> "Frame":
    """Decode raw bytes to Frame.

    Args:
        raw: Raw frame bytes

    Returns:
        Parsed Frame object
    """
    from .frame import Frame

    try:
        frame = Frame.from_bytes(raw)
        logger.debug(
            "Decoded frame: cmd=0x%02x%02x, len=%d",
            frame.cmd_hi,
            frame.cmd_lo,
            len(raw),
        )
        return frame
    except Exception as e:
        logger.exception("Failed to decode frame of length %d", len(raw))
        raise

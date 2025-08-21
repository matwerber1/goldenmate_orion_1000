"""Frame encoding/decoding and checksum functions."""

from .constants import START, END, PRODUCT_ID_DEFAULT
from typing import TYPE_CHECKING

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


def build_frame(product_id: int, address: int, cmd_hi: int, cmd_lo: int, payload: bytes) -> bytes:
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
    frame_data = bytes([
        START,
        product_id,
        address,
        data_len,
        cmd_hi,
        cmd_lo
    ]) + payload
    
    # Calculate checksum from product_id through payload
    checksum_data = frame_data[1:]  # Skip start byte
    checksum = xor_checksum(checksum_data)
    
    # Add checksum and end
    return frame_data + bytes([checksum, END])


def decode(raw: bytes) -> "Frame":
    """Decode raw bytes to Frame.
    
    Args:
        raw: Raw frame bytes
        
    Returns:
        Parsed Frame object
    """
    from .frame import Frame
    return Frame.from_bytes(raw)
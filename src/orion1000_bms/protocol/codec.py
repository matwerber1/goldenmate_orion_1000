"""Frame encoding/decoding and checksum functions."""


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
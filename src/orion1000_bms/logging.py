"""Logging utilities for BMS operations."""

import logging
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with library-friendly defaults.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if none exists (avoid duplicate handlers)
    if not logger.handlers:
        handler = logging.NullHandler()
        logger.addHandler(handler)
    
    return logger


def hex_dump(data: bytes, prefix: str = "") -> str:
    """Format bytes as hex dump for logging.
    
    Args:
        data: Bytes to format
        prefix: Optional prefix for each line
        
    Returns:
        Formatted hex string
    """
    if not data:
        return f"{prefix}<empty>"
    
    hex_str = data.hex().upper()
    # Add spaces between bytes
    formatted = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    return f"{prefix}{formatted}"


def log_frame_tx(logger: logging.Logger, frame: bytes, description: str = "TX") -> None:
    """Log transmitted frame at debug level.
    
    Args:
        logger: Logger instance
        frame: Frame bytes
        description: Frame description
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s: %s", description, hex_dump(frame))


def log_frame_rx(logger: logging.Logger, frame: bytes, description: str = "RX") -> None:
    """Log received frame at debug level.
    
    Args:
        logger: Logger instance
        frame: Frame bytes
        description: Frame description
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("%s: %s", description, hex_dump(frame))
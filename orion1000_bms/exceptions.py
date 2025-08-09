
from __future__ import annotations

class BMSError(Exception):
    """Base class for Orion1000 BMS errors."""

class BMSConnectionError(BMSError):
    """Socket-level connection error (connect, read, write, EOF)."""

class BMSReadTimeout(BMSError):
    """Timed out waiting for reply data."""

class BMSWriteTimeout(BMSError):
    """Timed out sending request data."""

class BMSProtocolError(BMSError):
    """Frame-level validation problem (bad preamble/length/checksum or unexpected cmd)."""

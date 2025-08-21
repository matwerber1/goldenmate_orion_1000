"""Exception hierarchy for BMS operations."""


class BmsError(Exception):
    """Base exception for all BMS-related errors."""
    pass


class TransportError(BmsError):
    """Transport layer communication error."""
    pass


class TimeoutError(TransportError):
    """Request timeout error."""
    pass


class ChecksumError(BmsError):
    """Frame checksum validation error."""
    pass


class FrameError(BmsError):
    """Frame parsing or validation error."""
    pass


class ProtocolError(BmsError):
    """Protocol-level error."""
    pass


class UnsupportedCommandError(BmsError):
    """Unsupported or unknown command error."""
    pass
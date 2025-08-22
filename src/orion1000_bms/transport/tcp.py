"""TCP transport implementation using pyserial."""

import time
import logging
from typing import Optional
import serial
from ..protocol.constants import START, END
from ..exceptions import TransportError, TimeoutError
from ..logging import get_logger, log_frame_tx, log_frame_rx
from .base import BaseTransport


class TcpTransport(BaseTransport):
    """TCP transport for BMS communication using pyserial."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 3.0,
        max_retries: int = 3,
        connection_strategy: str = "persistent",
        force_reconnect_interval: float = 300.0,
        buffer_settling_time: float = 0.1,
    ) -> None:
        """Initialize TCP transport.

        Args:
            host: TCP server hostname or IP
            port: TCP server port
            connect_timeout: Connection timeout (unused with pyserial)
            read_timeout: Read timeout in seconds
            max_retries: Maximum number of retries on timeout
            connection_strategy: "persistent" or "per_request"
            force_reconnect_interval: Force reconnect after this many seconds
            buffer_settling_time: Delay after connection establishment
        """
        super().__init__(max_retries=max_retries)
        self.host = host
        self.port = port
        self.read_timeout = read_timeout
        self.connection_strategy = connection_strategy
        self.force_reconnect_interval = force_reconnect_interval
        self.buffer_settling_time = buffer_settling_time
        self._serial: Optional[serial.Serial] = None
        self._connection_time: float = 0.0
        self._logger = get_logger(__name__)

    def _is_connection_alive(self) -> bool:
        """Check if connection is still alive."""
        if self._serial is None:
            return False
        
        try:
            # Check if connection is open and not stale
            if not self._serial.is_open:
                return False
            
            # Check connection age
            if (time.monotonic() - self._connection_time) > self.force_reconnect_interval:
                self._logger.debug("Connection aged out, forcing reconnect")
                return False
            
            return True
        except Exception:
            return False
    
    def _force_close(self) -> None:
        """Force close connection."""
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
            self._connection_time = 0.0
    
    def open_if_needed(self) -> None:
        """Open connection if not already open or validate existing connection."""
        # For per-request strategy, always use fresh connection
        if self.connection_strategy == "per_request":
            self._force_close()
        
        # Check if we need to reconnect
        if not self._is_connection_alive():
            self._force_close()
            
            try:
                url = f"socket://{self.host}:{self.port}"
                self._serial = serial.serial_for_url(
                    url,
                    timeout=self.read_timeout,
                    inter_byte_timeout=0.15,
                    write_timeout=1.0,
                )
                self._connection_time = time.monotonic()
                self._logger.debug("Connected to %s:%d", self.host, self.port)
                
                # Allow connection to settle
                if self.buffer_settling_time > 0:
                    time.sleep(self.buffer_settling_time)
                    
            except Exception as e:
                raise TransportError(
                    f"Connection failed to {self.host}:{self.port}: {e}"
                )

    def close(self) -> None:
        """Close the connection."""
        self._force_close()

    def __enter__(self) -> "TcpTransport":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic cleanup."""
        self.close()

    def _send_request_impl(
        self, payload: bytes, *, timeout: float | None = None
    ) -> bytes:
        """Implementation-specific request sending with enhanced error recovery.

        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout override

        Returns:
            Response frame bytes
        """
        last_error = None
        
        for attempt in range(2):  # Try twice with fresh connection on failure
            try:
                self.open_if_needed()

                if not self._serial:
                    raise TransportError("Serial connection not open")

                # Enhanced buffer clearing
                self._serial.reset_input_buffer()
                self._serial.reset_output_buffer()
                time.sleep(0.01)  # Brief settling time
                self._serial.reset_input_buffer()  # Clear again

                log_frame_tx(self._logger, payload)
                self._serial.write(payload)
                self._serial.flush()

                # Read response
                response = self._read_frame(timeout or self.read_timeout)
                log_frame_rx(self._logger, response)

                # Inter-request spacing per BMS protocol
                time.sleep(0.25)  # Slightly longer spacing

                return response
                
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                last_error = e
                self._logger.warning("Connection error on attempt %d: %s", attempt + 1, e)
                self._force_close()  # Force fresh connection on next attempt
                if attempt == 0:
                    time.sleep(0.5)  # Brief delay before retry
                continue
                
            except Exception as e:
                if "timeout" in str(e).lower():
                    # On timeout, force close connection for next request
                    if self.connection_strategy == "persistent":
                        self._force_close()
                    raise TimeoutError("Request timeout")
                
                # For other errors, also force close connection
                self._force_close()
                raise TransportError(f"Transport error: {e}")
        
        # If we get here, both attempts failed
        raise TransportError(f"Failed after 2 attempts, last error: {last_error}")

    def _read_exact(self, n: int, *, timeout_s: float = 1.0) -> bytes:
        """Read exactly n bytes or raise TimeoutError."""
        if not self._serial:
            raise TransportError("Serial connection not open")

        end_by = time.monotonic() + timeout_s
        buf = bytearray()
        consecutive_empty_reads = 0
        
        while len(buf) < n:
            if time.monotonic() > end_by:
                raise TimeoutError(f"Timeout reading {n} bytes (got {len(buf)})")
            
            try:
                chunk = self._serial.read(n - len(buf))
                if chunk:
                    buf.extend(chunk)
                    consecutive_empty_reads = 0
                else:
                    consecutive_empty_reads += 1
                    # If we get too many empty reads, the connection might be broken
                    if consecutive_empty_reads > 50:  # Reduced threshold
                        raise ConnectionResetError("Connection appears broken (too many empty reads)")
                    time.sleep(0.01)  # Slightly longer sleep
                    
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                raise ConnectionResetError(f"Connection error during read: {e}")
            except Exception as e:
                if "timeout" not in str(e).lower():
                    raise TransportError(f"Read error: {e}")
                raise TimeoutError(f"Timeout reading {n} bytes (got {len(buf)})")
                
        return bytes(buf)

    def _read_frame(self, timeout: float) -> bytes:
        """Read one complete frame with validation."""
        # Read header: [START PID addr len]
        header = self._read_exact(4, timeout_s=timeout)
        if header[0] != START:
            raise TransportError(f"Bad start byte: {header[0]:#04x}")

        length = header[3]
        if length < 4:
            raise TransportError(f"Length too small: {length}")

        # Read payload: data + checksum + end
        payload = self._read_exact(length, timeout_s=timeout)
        if payload[-1] != END:
            raise TransportError("Missing end byte")

        return header + payload

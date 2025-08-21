"""TCP transport implementation."""

import socket
import threading
import time
from typing import Optional
from ..protocol.constants import START, END
from ..exceptions import TransportError, TimeoutError
from ..logging import get_logger, log_frame_tx, log_frame_rx
from .base import BaseTransport


class TcpTransport(BaseTransport):
    """Synchronous TCP transport for BMS communication."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 3.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize TCP transport.

        Args:
            host: TCP server hostname or IP
            port: TCP server port
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
            max_retries: Maximum number of retries on timeout
        """
        super().__init__(max_retries=max_retries)
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._socket: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._logger = get_logger(__name__)

    def open_if_needed(self) -> None:
        """Open connection if not already open."""
        if self._socket is None:
            try:
                self._socket = socket.create_connection(
                    (self.host, self.port), timeout=self.connect_timeout
                )
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self._socket.settimeout(self.read_timeout)
                self._logger.debug("Connected to %s:%d", self.host, self.port)
            except socket.timeout:
                raise TimeoutError(f"Connection timeout to {self.host}:{self.port}")
            except OSError as e:
                raise TransportError(
                    f"Connection failed to {self.host}:{self.port}: {e}"
                )

    def close(self) -> None:
        """Close the connection."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def _send_request_impl(
        self, payload: bytes, *, timeout: float | None = None
    ) -> bytes:
        """Implementation-specific request sending.

        Args:
            payload: Request frame bytes to send
            timeout: Optional timeout override

        Returns:
            Response frame bytes
        """
        with self._lock:
            self.open_if_needed()

            old_timeout = None
            if timeout is not None and self._socket:
                old_timeout = self._socket.gettimeout()
                self._socket.settimeout(timeout)

            try:
                # Send request
                if not self._socket:
                    raise TransportError("Socket not connected")

                log_frame_tx(self._logger, payload)
                self._socket.sendall(payload)

                # Read response using two-phase strategy
                response = self._read_response()
                log_frame_rx(self._logger, response)
                return response
            except socket.timeout:
                raise TimeoutError("Request timeout")
            except OSError as e:
                raise TransportError(f"Transport error: {e}")
            finally:
                if old_timeout is not None and self._socket:
                    self._socket.settimeout(old_timeout)

    def _read_response(self) -> bytes:
        """Read complete response frame."""
        if not self._socket:
            raise TransportError("Socket not connected")

        # Phase 1: Read until we find start byte
        while True:
            byte = self._socket.recv(1)
            if not byte:
                raise TransportError("Connection closed")
            if byte[0] == START:
                break

        # Phase 2: Read header to get frame length
        header = self._socket.recv(3)  # product_id, address, data_len
        if len(header) != 3:
            raise TransportError("Incomplete header")

        data_len = header[2]

        # Phase 3: Read remaining data + checksum + end
        remaining = data_len + 2  # data + checksum + end
        data = self._socket.recv(remaining)
        if len(data) != remaining:
            raise TransportError("Incomplete frame")

        # Verify end byte
        if data[-1] != END:
            raise TransportError(f"Invalid end byte: {data[-1]:#x}")

        # Return complete frame
        return bytes([START]) + header + data

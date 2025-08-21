"""Fake BMS server for testing TCP transport."""

import socket
import threading
from typing import Dict, Callable
from orion1000_bms.protocol.codec import decode, build_frame
from orion1000_bms.protocol.constants import PRODUCT_ID_DEFAULT


class FakeBmsServer:
    """Fake BMS server that responds to commands with canned responses."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        """Initialize fake server.
        
        Args:
            host: Server host
            port: Server port (0 for auto-assign)
        """
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._handlers: Dict[int, Callable[[bytes], bytes]] = {}
        
        # Default handlers
        self._handlers[0x0300] = self._handle_read_total_voltage
        self._handlers[0x0302] = self._handle_read_current
    
    def start(self) -> None:
        """Start the fake server."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        
        # Update port if auto-assigned
        if self.port == 0:
            self.port = self._socket.getsockname()[1]
        
        self._socket.listen(1)
        self._running = True
        self._thread = threading.Thread(target=self._run_server)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the fake server."""
        self._running = False
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join()
    
    def _run_server(self) -> None:
        """Run server loop."""
        while self._running:
            try:
                if self._socket:
                    conn, addr = self._socket.accept()
                    self._handle_connection(conn)
            except OSError:
                break
    
    def _handle_connection(self, conn: socket.socket) -> None:
        """Handle client connection."""
        try:
            while self._running:
                # Read request frame
                data = conn.recv(1024)
                if not data:
                    break
                
                # Decode and handle request
                try:
                    frame = decode(data)
                    cmd_id = (frame.cmd_hi << 8) | frame.cmd_lo
                    
                    if cmd_id in self._handlers:
                        response = self._handlers[cmd_id](frame.payload)
                        conn.sendall(response)
                    else:
                        # Unknown command - send error response
                        error_response = build_frame(
                            PRODUCT_ID_DEFAULT, frame.address, 0xFF, 0xFF, b""
                        )
                        conn.sendall(error_response)
                except Exception:
                    # Invalid frame - close connection
                    break
        finally:
            conn.close()
    
    def _handle_read_total_voltage(self, payload: bytes) -> bytes:
        """Handle read total voltage command."""
        # Return fake voltage: 48.5V = 4850 (0x12F2)
        response_data = b"\x12\xF2"
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, response_data)
    
    def _handle_read_current(self, payload: bytes) -> bytes:
        """Handle read current command."""
        # Return fake current: 10.5A = 1050 (0x041A)
        response_data = b"\x04\x1A"
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x02, response_data)
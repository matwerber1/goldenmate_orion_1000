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
        
        # Default handlers for new protocol
        self._handlers[0xFF02] = self._handle_voltage_request
        self._handlers[0xFF03] = self._handle_current_status_request
    
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
    
    def _handle_voltage_request(self, payload: bytes) -> bytes:
        """Handle voltage request command."""
        # Return fake voltage data: 16 cells + 3 temps + string count
        import struct
        response_data = bytearray()
        # 16 cell voltages (3.0V each = 3000mV)
        for _ in range(16):
            response_data.extend(struct.pack('>H', 3000))
        # 3 temperatures (25.0°C each = 250 in 0.1°C)
        for _ in range(3):
            response_data.extend(struct.pack('>h', 250))
        # String count
        response_data.append(1)
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0xFF, 0x02, bytes(response_data))
    
    def _handle_current_status_request(self, payload: bytes) -> bytes:
        """Handle current status request command."""
        # Return fake current status data
        import struct
        response_data = bytearray()
        response_data.append(0x01)  # Status bits
        response_data.extend(struct.pack('>h', 105))  # Current 10.5A
        response_data.append(0x00)  # Protection status
        # 3 temperatures (25.0°C each)
        for _ in range(3):
            response_data.extend(struct.pack('>h', 250))
        response_data.append(0x03)  # MOS states
        response_data.append(0x01)  # Version
        response_data.append(0x00)  # Fault flags
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0xFF, 0x03, bytes(response_data))
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
        # Return fake voltage data in new format: metadata + cell voltages
        import struct
        response_data = bytearray()
        response_data.append(4)  # 4 cells in packet
        response_data.append(3)  # 3 temp probes
        response_data.append(4)  # 4 total system cells
        # 4 cell voltages (3.0V each = 3000mV)
        for _ in range(4):
            response_data.extend(struct.pack('>H', 3000))
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0xFF, 0x02, bytes(response_data))
    
    def _handle_current_status_request(self, payload: bytes) -> bytes:
        """Handle current status request command."""
        # Return fake current status data in new format
        import struct
        response_data = bytearray()
        response_data.append(0x01)  # Status flags: discharge_active=1
        response_data.extend(struct.pack('>H', 1050))  # Current 1050 * 10mA = 10.5A
        response_data.append(0x00)  # OV protection
        response_data.append(0x00)  # UV protection
        response_data.append(0x00)  # Temp protection
        response_data.append(0x00)  # General protection
        response_data.append(3)     # 3 temperature probes
        response_data.append(65)    # Temp 1: 65 - 40 = 25°C
        response_data.append(66)    # Temp 2: 66 - 40 = 26°C
        response_data.append(64)    # Temp 3: 64 - 40 = 24°C
        response_data.append(0x01)  # Software version
        response_data.append(0x03)  # MOS states
        response_data.append(0x00)  # Failure status
        return build_frame(PRODUCT_ID_DEFAULT, 0x01, 0xFF, 0x03, bytes(response_data))
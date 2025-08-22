"""Demo tests for TCP transport reliability improvements."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import serial

from orion1000_bms.transport.tcp import TcpTransport
from orion1000_bms.exceptions import TransportError, TimeoutError


class TestTransportReliabilityDemo:
    """Demo tests for enhanced TCP transport reliability."""

    def test_connection_strategy_persistent(self):
        """Test persistent connection strategy."""
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            connection_strategy="persistent",
            force_reconnect_interval=10.0
        )
        
        assert transport.connection_strategy == "persistent"
        assert transport.force_reconnect_interval == 10.0

    def test_connection_strategy_per_request(self):
        """Test per-request connection strategy."""
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            connection_strategy="per_request",
            buffer_settling_time=0.2
        )
        
        assert transport.connection_strategy == "per_request"
        assert transport.buffer_settling_time == 0.2

    @patch('serial.serial_for_url')
    def test_connection_health_monitoring(self, mock_serial_for_url):
        """Test connection health monitoring."""
        # Setup mock serial connection
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport("127.0.0.1", 1234)
        
        # First connection should work
        transport.open_if_needed()
        assert transport._is_connection_alive()
        
        # Simulate connection closed
        mock_serial.is_open = False
        assert not transport._is_connection_alive()

    @patch('serial.serial_for_url')
    def test_connection_age_timeout(self, mock_serial_for_url):
        """Test connection age-based reconnection."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            force_reconnect_interval=0.1  # Very short interval
        )
        
        # Manually set up connection state
        transport._serial = mock_serial
        transport._connection_time = time.monotonic()
        
        # Should be alive initially
        assert transport._is_connection_alive()
        
        # Manually set old connection time to simulate age timeout
        transport._connection_time = time.monotonic() - 1.0  # 1 second ago (older than 0.1s interval)
        assert not transport._is_connection_alive()

    @patch('serial.serial_for_url')
    def test_per_request_strategy_forces_reconnect(self, mock_serial_for_url):
        """Test that per-request strategy forces reconnection."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            connection_strategy="per_request"
        )
        
        # First connection
        transport.open_if_needed()
        first_connection_time = transport._connection_time
        
        # Second call should force new connection
        transport.open_if_needed()
        second_connection_time = transport._connection_time
        
        # Connection time should be different (new connection)
        assert second_connection_time > first_connection_time

    @patch('serial.serial_for_url')
    def test_buffer_settling_time(self, mock_serial_for_url):
        """Test buffer settling time is applied."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            buffer_settling_time=0.1
        )
        
        start_time = time.time()
        transport.open_if_needed()
        end_time = time.time()
        
        # Should have taken at least the settling time
        assert (end_time - start_time) >= 0.1

    @patch('serial.serial_for_url')
    def test_connection_retry_on_failure(self, mock_serial_for_url):
        """Test connection retry logic."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.reset_input_buffer = Mock()
        mock_serial.reset_output_buffer = Mock()
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport("127.0.0.1", 1234)
        
        # Mock _read_frame to fail first time, succeed second time
        with patch.object(transport, '_read_frame') as mock_read_frame:
            mock_read_frame.side_effect = [
                ConnectionResetError("Connection lost"),  # First attempt fails
                b'response_data'  # Second attempt succeeds
            ]
            
            # Should succeed after retry
            result = transport._send_request_impl(b'test_payload')
            assert result == b'response_data'
            
            # Should have been called twice (original + retry)
            assert mock_read_frame.call_count == 2

    @patch('serial.serial_for_url')
    def test_enhanced_buffer_clearing(self, mock_serial_for_url):
        """Test enhanced buffer clearing logic."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.reset_input_buffer = Mock()
        mock_serial.reset_output_buffer = Mock()
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport("127.0.0.1", 1234)
        
        with patch.object(transport, '_read_frame', return_value=b'response'):
            transport._send_request_impl(b'test_payload')
            
            # Should clear input buffer twice (enhanced clearing)
            assert mock_serial.reset_input_buffer.call_count == 2
            assert mock_serial.reset_output_buffer.call_count == 1

    @patch('serial.serial_for_url')
    def test_connection_error_detection(self, mock_serial_for_url):
        """Test connection error detection in _read_exact."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.read.side_effect = ConnectionResetError("Connection broken")
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport("127.0.0.1", 1234)
        transport._serial = mock_serial
        
        # Should detect and raise ConnectionResetError
        with pytest.raises(ConnectionResetError):
            transport._read_exact(10)

    @patch('serial.serial_for_url')
    def test_empty_read_detection(self, mock_serial_for_url):
        """Test detection of too many empty reads."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.read.return_value = b''  # Always return empty
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport("127.0.0.1", 1234)
        transport._serial = mock_serial
        
        # Should detect broken connection after too many empty reads
        with pytest.raises(ConnectionResetError, match="Connection appears broken"):
            transport._read_exact(10, timeout_s=1.0)

    def test_force_close_cleanup(self):
        """Test force close properly cleans up."""
        transport = TcpTransport("127.0.0.1", 1234)
        
        # Setup mock connection
        mock_serial = Mock()
        transport._serial = mock_serial
        transport._connection_time = time.time()
        
        # Force close
        transport._force_close()
        
        # Should clean up properly
        assert transport._serial is None
        assert transport._connection_time == 0.0
        mock_serial.close.assert_called_once()

    def test_force_close_handles_exceptions(self):
        """Test force close handles exceptions gracefully."""
        transport = TcpTransport("127.0.0.1", 1234)
        
        # Setup mock connection that raises on close
        mock_serial = Mock()
        mock_serial.close.side_effect = Exception("Close failed")
        transport._serial = mock_serial
        
        # Should not raise exception
        transport._force_close()
        
        # Should still clean up
        assert transport._serial is None

    @patch('serial.serial_for_url')
    def test_timeout_forces_connection_close(self, mock_serial_for_url):
        """Test that timeouts force connection close in persistent mode."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.reset_input_buffer = Mock()
        mock_serial.reset_output_buffer = Mock()
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial_for_url.return_value = mock_serial
        
        transport = TcpTransport(
            "127.0.0.1", 
            1234,
            connection_strategy="persistent"
        )
        
        with patch.object(transport, '_read_frame') as mock_read_frame:
            mock_read_frame.side_effect = TimeoutError("Request timeout")
            
            # Should raise TimeoutError and close connection
            with pytest.raises(TimeoutError):
                transport._send_request_impl(b'test_payload')
            
            # Connection should be closed
            assert transport._serial is None

    def test_context_manager_cleanup(self):
        """Test context manager properly cleans up."""
        transport = TcpTransport("127.0.0.1", 1234)
        
        # Setup mock connection
        mock_serial = Mock()
        transport._serial = mock_serial
        
        # Use context manager
        with transport:
            pass
        
        # Should be cleaned up
        assert transport._serial is None
        mock_serial.close.assert_called_once()
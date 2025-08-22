"""Demo tests for main.py functionality."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

# Import main module
sys.path.insert(0, "/Users/mathewwerber/projects/orionv2")
import main


@pytest.fixture
def mock_transport() -> Mock:
    """Create a mock transport for testing."""
    transport = Mock()
    transport.host = "192.168.99.93"
    transport.port = 26
    return transport


@pytest.fixture
def mock_client(mock_transport) -> Mock:
    """Create a mock client for testing."""
    client = Mock()
    client.close = Mock()
    return client


@pytest.fixture
def sample_voltage_response() -> Mock:
    """Sample voltage response data."""
    response = Mock()
    response.to_dict.return_value = {
        "cell_voltages": [3.272, 3.274, 3.273, 3.276],
        "cell_count_in_packet": 4,
        "temp_probe_count": 6,
        "total_system_cells": 4,
        "_metadata": {
            "tcp_host": "192.168.99.93",
            "tcp_port": 26,
            "request_timestamp": 1755853536.656231,
            "response_timestamp": 1755853540.280509,
            "response_time_ms": 3624.28,
        },
    }
    return response


@pytest.fixture
def sample_current_response() -> Mock:
    """Sample current status response data."""
    response = Mock()
    response.to_dict.return_value = {
        "status_flags": {
            "discharge_active": False,
            "charge_active": False,
            "mos_temp_present": True,
            "ambient_temp_present": True,
        },
        "current": 0.0,
        "overvoltage_protection": {
            "cell_ov": False,
            "pack_ov": False,
            "full_charge_protection": False,
        },
        "undervoltage_protection": {"cell_uv": False, "pack_uv": False},
        "temperature_protection": {
            "charge_temp": False,
            "discharge_temp": False,
            "mos_over_temp": False,
            "high_temp": False,
            "low_temp": False,
        },
        "general_protection": {
            "discharge_short_circuit": False,
            "discharge_oc": False,
            "charge_oc": False,
            "ambient_high_temp": False,
            "ambient_low_temp": False,
        },
        "temp_probe_count": 6,
        "temperatures": [21.0, 22.0, 21.0, 21.0, 22.0, 21.0],
        "software_version": 0,
        "mos_state": {"discharge_mos_on": False, "charge_mos_on": False},
        "failure_status": {
            "temp_acquisition_fail": False,
            "voltage_acquisition_fail": False,
            "discharge_mos_fail": False,
            "charge_mos_fail": False,
        },
        "_metadata": {
            "tcp_host": "192.168.99.93",
            "tcp_port": 26,
            "request_timestamp": 1755853541.2893949,
            "response_timestamp": 1755853541.6186528,
            "response_time_ms": 329.26,
        },
    }
    return response


@pytest.fixture
def sample_capacity_response() -> dict:
    """Sample capacity status response data."""
    response = Mock()
    response.to_dict.return_value = {
        "soc": 96,
        "cycle_count": 0,
        "design_capacity_high": 1,
        "design_capacity_low": 34464,
        "full_charge_capacity_high": 1,
        "full_charge_capacity_low": 34464,
        "remaining_capacity_high": 1,
        "remaining_capacity_low": 30454,
        "remaining_discharge_time": 65535,
        "remaining_charge_time": 65535,
        "charge_interval_current": 0,
        "charge_interval_max": 0,
        "pack_voltage": 74.36,
        "max_cell_voltage": 52.236,
        "min_cell_voltage": 51.213,
        "hardware_version": 0,
        "scheme_id": 0,
        "reserved": "000000",
        "_metadata": {
            "tcp_host": "192.168.99.93",
            "tcp_port": 26,
            "request_timestamp": 1755853570.954936,
            "response_timestamp": 1755853571.256609,
            "response_time_ms": 301.67,
        },
    }
    return response


@pytest.fixture
def sample_serial_response() -> Mock:
    """Sample serial number response data."""
    response = Mock()
    response.to_dict.return_value = {
        "serial_number": "ORN1000-TEST-001",
        "_metadata": {
            "tcp_host": "192.168.99.93",
            "tcp_port": 26,
            "request_timestamp": 1755853572.2628732,
            "response_timestamp": 1755853572.509866,
            "response_time_ms": 246.99,
        },
    }
    return response


class TestMainDemo:
    """Demo tests for main.py functionality."""

    @patch("main.TcpTransport")
    @patch("main.BmsClient")
    @patch("builtins.print")
    def test_successful_data_collection(
        self,
        mock_print,
        mock_bms_client_class,
        mock_tcp_transport_class,
        sample_voltage_response,
        sample_current_response,
        sample_capacity_response,
        sample_serial_response,
    ) -> None:
        """Test successful collection of all BMS data."""
        # Setup mocks
        mock_transport = Mock()
        mock_tcp_transport_class.return_value = mock_transport

        mock_client = Mock()
        mock_bms_client_class.return_value = mock_client

        # Configure client method returns
        mock_client.read_voltage_data.return_value = sample_voltage_response
        mock_client.read_current_status.return_value = sample_current_response
        mock_client.read_capacity_status.return_value = sample_capacity_response

        # Mock serial number request
        with patch(
            "orion1000_bms.commands.serial_number_request.SerialNumberRequest"
        ) as mock_serial_request_class:
            mock_serial_request = Mock()
            mock_serial_request_class.return_value = mock_serial_request
            mock_client.request.return_value = sample_serial_response

            # Run main function
            main.main()

        # Verify transport was created with correct parameters
        mock_tcp_transport_class.assert_called_once_with(
            host="192.168.99.93",
            port=26,
            connection_strategy="per_request",
            buffer_settling_time=0.2,
            read_timeout=5.0,
        )

        # Verify client was created
        mock_bms_client_class.assert_called_once_with(mock_transport, address=0x01)

        # Verify all commands were called
        mock_client.read_voltage_data.assert_called_once()
        mock_client.read_current_status.assert_called_once()
        mock_client.read_capacity_status.assert_called_once()
        mock_client.request.assert_called_once()

        # Verify client was closed
        mock_client.close.assert_called_once()

        # Verify output contains expected elements
        print_calls = [
            str(call.args[0]) if call.args else str(call)
            for call in mock_print.call_args_list
        ]
        output_text = "\n".join(print_calls)

        assert "=== Orion 1000 BMS Data Collection ===" in output_text
        assert "Connected to: 192.168.99.93:26" in output_text
        assert "✓ Voltage Data collected successfully" in output_text
        assert "✓ Current Status collected successfully" in output_text
        assert "✓ Capacity Status collected successfully" in output_text
        assert "✓ Serial Number collected successfully" in output_text
        assert "=== Complete BMS Data (JSON) ===" in output_text
        assert "=== Summary ===" in output_text

    @patch("main.TcpTransport")
    @patch("main.BmsClient")
    @patch("builtins.print")
    def test_partial_failure_handling(
        self,
        mock_print,
        mock_bms_client_class,
        mock_tcp_transport_class,
        sample_voltage_response,
        sample_current_response,
    ) -> None:
        """Test handling of partial command failures."""
        # Setup mocks
        mock_transport = Mock()
        mock_tcp_transport_class.return_value = mock_transport

        mock_client = Mock()
        mock_bms_client_class.return_value = mock_client

        # Configure some successes and some failures
        mock_client.read_voltage_data.return_value = sample_voltage_response
        mock_client.read_current_status.return_value = sample_current_response
        mock_client.read_capacity_status.side_effect = Exception("Capacity read failed")
        mock_client.request.side_effect = Exception("Serial number read failed")

        # Run main function
        main.main()

        # Verify client was still closed despite errors
        mock_client.close.assert_called_once()

        # Verify output contains both successes and failures
        print_calls = [
            str(call.args[0]) if call.args else str(call)
            for call in mock_print.call_args_list
        ]
        output_text = "\n".join(print_calls)

        assert "✓ Voltage Data collected successfully" in output_text
        assert "✓ Current Status collected successfully" in output_text
        assert "✗ Failed to read Capacity Status: Capacity read failed" in output_text
        assert (
            "✗ Failed to read Serial Number: Serial number read failed" in output_text
        )

    @patch("main.TcpTransport")
    @patch("main.BmsClient")
    @patch("builtins.print")
    def test_connection_error_handling(
        self, mock_print, mock_bms_client_class, mock_tcp_transport_class
    ) -> None:
        """Test handling of connection errors."""
        # Setup mocks
        mock_transport = Mock()
        mock_tcp_transport_class.return_value = mock_transport

        mock_client = Mock()
        mock_bms_client_class.return_value = mock_client

        # Simulate connection error
        mock_client.read_voltage_data.side_effect = Exception("Connection timeout")

        # Run main function
        main.main()

        # Verify client was still closed
        mock_client.close.assert_called_once()

        # Verify error was handled
        print_calls = [
            str(call.args[0]) if call.args else str(call)
            for call in mock_print.call_args_list
        ]
        output_text = "\n".join(print_calls)

        assert "✗ Failed to read Voltage Data: Connection timeout" in output_text

    @patch("main.TcpTransport")
    @patch("main.BmsClient")
    @patch("builtins.print")
    def test_json_output_format(
        self,
        mock_print,
        mock_bms_client_class,
        mock_tcp_transport_class,
        sample_voltage_response,
    ) -> None:
        """Test that JSON output is properly formatted."""
        # Setup mocks
        mock_transport = Mock()
        mock_tcp_transport_class.return_value = mock_transport

        mock_client = Mock()
        mock_bms_client_class.return_value = mock_client

        # Configure minimal successful response
        mock_client.read_voltage_data.return_value = sample_voltage_response
        mock_client.read_current_status.side_effect = Exception("Failed")
        mock_client.read_capacity_status.side_effect = Exception("Failed")
        mock_client.request.side_effect = Exception("Failed")

        # Run main function
        main.main()

        # Find JSON output in print calls
        print_calls = [
            str(call.args[0]) if call.args else str(call)
            for call in mock_print.call_args_list
        ]

        # Look for JSON in the output - it should be a single call with the JSON string
        json_text = None
        for call_text in print_calls:
            if call_text.strip().startswith("{") and "voltage_data" in call_text:
                json_text = call_text
                break

        assert json_text is not None, "JSON output not found in print calls"
        parsed_json = json.loads(json_text)

        # Verify structure
        assert "voltage_data" in parsed_json
        assert "current_status" in parsed_json
        assert "capacity_status" in parsed_json
        assert "serial_number" in parsed_json

        # Verify voltage data structure
        voltage_data = parsed_json["voltage_data"]
        assert "cell_voltages" in voltage_data
        assert "_metadata" in voltage_data
        assert voltage_data["cell_count_in_packet"] == 4

    @patch("main.TcpTransport")
    @patch("main.BmsClient")
    @patch("builtins.print")
    def test_summary_calculations(
        self,
        mock_print,
        mock_bms_client_class,
        mock_tcp_transport_class,
        sample_voltage_response,
        sample_current_response,
        sample_serial_response,
    ) -> None:
        """Test summary calculations are correct."""
        # Setup mocks
        mock_transport = Mock()
        mock_tcp_transport_class.return_value = mock_transport

        mock_client = Mock()
        mock_bms_client_class.return_value = mock_client

        # Configure responses
        mock_client.read_voltage_data.return_value = sample_voltage_response
        mock_client.read_current_status.return_value = sample_current_response
        mock_client.read_capacity_status.side_effect = Exception("Failed")
        mock_client.request.return_value = sample_serial_response

        # Run main function
        main.main()

        # Verify summary calculations
        print_calls = [
            str(call.args[0]) if call.args else str(call)
            for call in mock_print.call_args_list
        ]
        output_text = "\n".join(print_calls)

        # Check voltage calculation (3.272 + 3.274 + 3.273 + 3.276 = 13.095)
        assert "Total Pack Voltage: 13.10V" in output_text
        assert "Cell Count: 4" in output_text
        assert "Current: 0.00A" in output_text
        assert "Serial Number: ORN1000-TEST-001" in output_text

    @patch("main.logging.basicConfig")
    def test_logging_configuration(self, mock_logging_config) -> None:
        """Test that logging is configured correctly."""
        with patch("main.TcpTransport"), patch("main.BmsClient"):
            main.main()

        # Verify logging was configured
        mock_logging_config.assert_called_once()
        call_args = mock_logging_config.call_args

        # Check logging level and format
        assert call_args[1]["level"] == main.logging.INFO
        assert (
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            in call_args[1]["format"]
        )

"""Unit tests for BMS client."""

import time
import struct
from unittest.mock import Mock, patch
import pytest

from orion1000_bms.client import BmsClient
from orion1000_bms.commands import (
    VoltageRequest,
    VoltageResponse,
    CurrentStatusRequest,
    CurrentStatusResponse,
)
from orion1000_bms.exceptions import UnsupportedCommandError
from orion1000_bms.protocol.codec import build_frame
from orion1000_bms.protocol.constants import PRODUCT_ID_DEFAULT, COMMAND_HIGH


@pytest.fixture
def mock_transport() -> Mock:
    """Create mock transport."""
    return Mock()


@pytest.fixture
def client(mock_transport: Mock) -> BmsClient:
    """Create BMS client with mock transport."""
    return BmsClient(mock_transport, min_spacing_s=0.0)  # Disable spacing for tests


@pytest.mark.phase6
def test_client_initialization(mock_transport: Mock) -> None:
    """Test client initialization."""
    client = BmsClient(mock_transport, product_id=0xAA, address=0x02, min_spacing_s=0.5)
    assert client._transport is mock_transport
    assert client._product_id == 0xAA
    assert client._address == 0x02
    assert client._min_spacing_s == 0.5


@pytest.mark.phase6
def test_request_basic(client: BmsClient, mock_transport: Mock) -> None:
    """Test basic request/response."""
    # Create voltage response payload
    payload = bytearray()
    # Add 16 cell voltages (3000 mV each)
    for i in range(16):
        payload.extend(struct.pack(">H", 3000))
    # Add 3 temperatures (25.0°C each)
    for i in range(3):
        payload.extend(struct.pack(">h", 250))
    # Add string count
    payload.append(1)
    
    # Mock response frame
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x02, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    # Send request
    req = VoltageRequest()
    resp = client.request(req)

    # Verify transport called correctly
    mock_transport.send_request.assert_called_once()
    call_args = mock_transport.send_request.call_args
    assert call_args[1]["timeout"] is None

    # Verify response
    assert isinstance(resp, VoltageResponse)
    assert len(resp.cell_voltages) == 16
    assert resp.cell_voltages[0] == 3.0


@pytest.mark.phase6
def test_request_with_timeout(client: BmsClient, mock_transport: Mock) -> None:
    """Test request with timeout."""
    # Create voltage response payload
    payload = bytearray()
    for i in range(16):
        payload.extend(struct.pack(">H", 3000))
    for i in range(3):
        payload.extend(struct.pack(">h", 250))
    payload.append(1)
    
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x02, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    req = VoltageRequest()
    client.request(req, timeout=5.0)

    call_args = mock_transport.send_request.call_args
    assert call_args[1]["timeout"] == 5.0


@pytest.mark.phase6
def test_request_unsupported_command(client: BmsClient) -> None:
    """Test request with unsupported command."""
    req = Mock()
    req.command_id = 0x9999  # Non-existent command
    req.to_payload.return_value = b""

    with pytest.raises(UnsupportedCommandError, match="Unknown command"):
        client.request(req)


@pytest.mark.phase6
def test_request_command_mismatch(client: BmsClient, mock_transport: Mock) -> None:
    """Test response with mismatched command."""
    # Response with wrong command (0x03 instead of 0x02)
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x03, b"\x01\xe5")
    mock_transport.send_request.return_value = response_frame

    req = VoltageRequest()  # Command 0x02
    with pytest.raises(UnsupportedCommandError, match="Response command mismatch"):
        client.request(req)


@pytest.mark.phase6
def test_request_spacing() -> None:
    """Test minimum request spacing enforcement."""
    mock_transport = Mock()
    
    # Create voltage response payload
    payload = bytearray()
    for i in range(16):
        payload.extend(struct.pack(">H", 3000))
    for i in range(3):
        payload.extend(struct.pack(">h", 250))
    payload.append(1)
    
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x02, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    client = BmsClient(mock_transport, min_spacing_s=0.1)

    req = VoltageRequest()

    # First request
    start_time = time.time()
    client.request(req)
    first_time = time.time()

    # Second request should be delayed
    client.request(req)
    second_time = time.time()

    # Should have waited at least min_spacing_s
    elapsed = second_time - first_time
    assert elapsed >= 0.1


@pytest.mark.phase6
def test_read_total_voltage(client: BmsClient, mock_transport: Mock) -> None:
    """Test read total voltage helper method."""
    # Create voltage response payload with cell voltages that sum to 48.5V
    payload = bytearray()
    # 16 cells at 3.03125V each = 48.5V total
    for i in range(16):
        payload.extend(struct.pack(">H", 3031))  # 3.031V in mV
    for i in range(3):
        payload.extend(struct.pack(">h", 250))
    payload.append(1)
    
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x02, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    voltage = client.read_total_voltage()
    assert abs(voltage - 48.496) < 0.01  # Allow for rounding


@pytest.mark.phase6
def test_read_current(client: BmsClient, mock_transport: Mock) -> None:
    """Test read current helper method."""
    # Create current status response payload
    payload = bytearray()
    payload.append(0x01)  # Status bits
    payload.extend(struct.pack(">h", 105))  # Current 10.5A
    payload.append(0x00)  # Protection status
    for i in range(3):
        payload.extend(struct.pack(">h", 250))  # Temperatures
    payload.append(0x03)  # MOS states
    payload.append(0x01)  # Version
    payload.append(0x00)  # Fault flags
    
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x03, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    current = client.read_current()
    assert current == 10.5


@pytest.mark.phase6
def test_read_cell_voltage(client: BmsClient, mock_transport: Mock) -> None:
    """Test read cell voltage helper method."""
    # Create voltage response payload
    payload = bytearray()
    # Set cell 3 to 3.456V, others to 3.0V
    for i in range(16):
        if i == 3:
            payload.extend(struct.pack(">H", 3456))  # 3.456V in mV
        else:
            payload.extend(struct.pack(">H", 3000))  # 3.0V in mV
    for i in range(3):
        payload.extend(struct.pack(">h", 250))
    payload.append(1)
    
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, COMMAND_HIGH, 0x02, bytes(payload))
    mock_transport.send_request.return_value = response_frame

    voltage = client.read_cell_voltage(3)
    assert voltage == 3.456


@pytest.mark.phase6
def test_close(client: BmsClient, mock_transport: Mock) -> None:
    """Test client close method."""
    client.close()
    mock_transport.close.assert_called_once()

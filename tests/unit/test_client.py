"""Unit tests for BMS client."""

import time
from unittest.mock import Mock, patch
import pytest

from orion1000_bms.client import BmsClient
from orion1000_bms.commands.read_total_voltage import (
    ReadTotalVoltageRequest,
    ReadTotalVoltageResponse,
)
from orion1000_bms.commands.read_current import ReadCurrentRequest, ReadCurrentResponse
from orion1000_bms.commands.read_cell_voltage import (
    ReadCellVoltageRequest,
    ReadCellVoltageResponse,
)
from orion1000_bms.exceptions import UnsupportedCommandError
from orion1000_bms.protocol.codec import build_frame
from orion1000_bms.protocol.constants import PRODUCT_ID_DEFAULT


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
    client = BmsClient(
        mock_transport, product_id=0xAA, address=0x02, min_spacing_s=0.5
    )
    assert client._transport is mock_transport
    assert client._product_id == 0xAA
    assert client._address == 0x02
    assert client._min_spacing_s == 0.5


@pytest.mark.phase6
def test_request_basic(client: BmsClient, mock_transport: Mock) -> None:
    """Test basic request/response."""
    # Mock response frame
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"\x01\xE5")
    mock_transport.send_request.return_value = response_frame

    # Send request
    req = ReadTotalVoltageRequest()
    resp = client.request(req)

    # Verify transport called correctly
    mock_transport.send_request.assert_called_once()
    call_args = mock_transport.send_request.call_args
    assert call_args[1]["timeout"] is None

    # Verify response
    assert isinstance(resp, ReadTotalVoltageResponse)
    assert resp.voltage == 48.5


@pytest.mark.phase6
def test_request_with_timeout(client: BmsClient, mock_transport: Mock) -> None:
    """Test request with timeout."""
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"\x01\xE5")
    mock_transport.send_request.return_value = response_frame

    req = ReadTotalVoltageRequest()
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
    # Response with wrong command
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x01, b"\x01\xE5")
    mock_transport.send_request.return_value = response_frame

    req = ReadTotalVoltageRequest()  # Command 0x0300
    with pytest.raises(UnsupportedCommandError, match="Response command mismatch"):
        client.request(req)


@pytest.mark.phase6
def test_request_spacing() -> None:
    """Test minimum request spacing enforcement."""
    mock_transport = Mock()
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"\x01\xE5")
    mock_transport.send_request.return_value = response_frame

    client = BmsClient(mock_transport, min_spacing_s=0.1)

    req = ReadTotalVoltageRequest()

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
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"\x01\xE5")
    mock_transport.send_request.return_value = response_frame

    voltage = client.read_total_voltage()
    assert voltage == 48.5


@pytest.mark.phase6
def test_read_current(client: BmsClient, mock_transport: Mock) -> None:
    """Test read current helper method."""
    response_frame = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x02, b"\x00\x69")
    mock_transport.send_request.return_value = response_frame

    current = client.read_current()
    assert current == 10.5


@pytest.mark.phase6
def test_read_cell_voltage(client: BmsClient, mock_transport: Mock) -> None:
    """Test read cell voltage helper method."""
    response_frame = build_frame(
        PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x01, b"\x03\x0D\x80"
    )
    mock_transport.send_request.return_value = response_frame

    voltage = client.read_cell_voltage(3)
    assert voltage == 3.456


@pytest.mark.phase6
def test_close(client: BmsClient, mock_transport: Mock) -> None:
    """Test client close method."""
    client.close()
    mock_transport.close.assert_called_once()
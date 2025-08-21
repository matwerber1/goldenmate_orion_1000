"""Integration tests for BMS client."""

import pytest
from typing import Iterator

from orion1000_bms.client import BmsClient
from orion1000_bms.transport.tcp import TcpTransport
from .fakes.fake_bms_server import FakeBmsServer


@pytest.fixture
def fake_server() -> Iterator[FakeBmsServer]:
    """Create and start fake BMS server."""
    server = FakeBmsServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def client(fake_server: FakeBmsServer) -> Iterator[BmsClient]:
    """Create BMS client connected to fake server."""
    transport = TcpTransport("127.0.0.1", fake_server.port)
    client = BmsClient(transport, min_spacing_s=0.0)  # Disable spacing for tests
    yield client
    client.close()


@pytest.mark.phase6
def test_client_read_total_voltage(client: BmsClient) -> None:
    """Test client read total voltage integration."""
    voltage = client.read_total_voltage()
    assert voltage == 485.0  # From fake server


@pytest.mark.phase6
def test_client_read_current(client: BmsClient) -> None:
    """Test client read current integration."""
    current = client.read_current()
    assert current == 105.0  # From fake server


@pytest.mark.phase6
def test_client_multiple_requests(client: BmsClient) -> None:
    """Test multiple requests work correctly."""
    voltage1 = client.read_total_voltage()
    current = client.read_current()
    voltage2 = client.read_total_voltage()

    assert voltage1 == 485.0
    assert current == 105.0
    assert voltage2 == 485.0


@pytest.mark.phase6
def test_client_with_timeout(client: BmsClient) -> None:
    """Test client requests with timeout."""
    voltage = client.read_total_voltage(timeout=1.0)
    assert voltage == 485.0
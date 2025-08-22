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
def test_client_read_voltage_data(client: BmsClient) -> None:
    """Test client read voltage data integration."""
    voltage_data = client.read_voltage_data()
    total_voltage = sum(voltage_data.cell_voltages)
    assert total_voltage == 12.0  # 4 cells * 3.0V each


@pytest.mark.phase6
def test_client_read_current_status(client: BmsClient) -> None:
    """Test client read current status integration."""
    current_status = client.read_current_status()
    assert current_status.current == 10.5  # From fake server


@pytest.mark.phase6
def test_client_multiple_requests(client: BmsClient) -> None:
    """Test multiple requests work correctly."""
    voltage_data1 = client.read_voltage_data()
    current_status = client.read_current_status()
    voltage_data2 = client.read_voltage_data()

    assert sum(voltage_data1.cell_voltages) == 12.0
    assert current_status.current == 10.5
    assert sum(voltage_data2.cell_voltages) == 12.0


@pytest.mark.phase6
def test_client_with_timeout(client: BmsClient) -> None:
    """Test client requests with timeout."""
    voltage_data = client.read_voltage_data(timeout=1.0)
    total_voltage = sum(voltage_data.cell_voltages)
    assert total_voltage == 12.0

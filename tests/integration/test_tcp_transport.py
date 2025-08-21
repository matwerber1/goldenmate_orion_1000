"""Integration tests for TCP transport."""

import pytest
import time
from typing import Iterator
from orion1000_bms.transport.tcp import TcpTransport
from orion1000_bms.protocol.codec import build_frame, decode
from orion1000_bms.protocol.constants import PRODUCT_ID_DEFAULT
from orion1000_bms.exceptions import TransportError, TimeoutError
from .fakes.fake_bms_server import FakeBmsServer


@pytest.fixture
def fake_server() -> Iterator[FakeBmsServer]:
    """Create and start fake BMS server."""
    server = FakeBmsServer()
    server.start()
    yield server
    server.stop()


@pytest.mark.phase3
def test_tcp_transport_basic_request(fake_server: FakeBmsServer) -> None:
    """Test basic TCP transport request/response."""
    transport = TcpTransport("127.0.0.1", fake_server.port)

    # Send read total voltage command
    request = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    response_bytes = transport.send_request(request)

    # Decode response
    response = decode(response_bytes)
    assert response.cmd_hi == 0x03
    assert response.cmd_lo == 0x00
    assert len(response.payload) == 2  # Voltage data

    transport.close()


@pytest.mark.phase3
def test_tcp_transport_multiple_requests(fake_server: FakeBmsServer) -> None:
    """Test multiple requests on same connection."""
    transport = TcpTransport("127.0.0.1", fake_server.port)

    # First request - total voltage
    request1 = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    response1 = transport.send_request(request1)
    frame1 = decode(response1)
    assert frame1.cmd_hi == 0x03 and frame1.cmd_lo == 0x00

    # Second request - current
    request2 = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x02, b"")
    response2 = transport.send_request(request2)
    frame2 = decode(response2)
    assert frame2.cmd_hi == 0x03 and frame2.cmd_lo == 0x02

    transport.close()


@pytest.mark.phase3
def test_tcp_transport_timeout() -> None:
    """Test transport timeout on non-existent server."""
    transport = TcpTransport("127.0.0.1", 9999, connect_timeout=0.1)

    request = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")

    with pytest.raises((TransportError, TimeoutError)):
        transport.send_request(request)


@pytest.mark.phase3
def test_tcp_transport_auto_reconnect(fake_server: FakeBmsServer) -> None:
    """Test transport handles connection close and reconnect."""
    transport = TcpTransport("127.0.0.1", fake_server.port)

    # First request
    request = build_frame(PRODUCT_ID_DEFAULT, 0x01, 0x03, 0x00, b"")
    response1 = transport.send_request(request)
    assert decode(response1).cmd_hi == 0x03

    # Close connection
    transport.close()

    # Second request should auto-reconnect
    response2 = transport.send_request(request)
    assert decode(response2).cmd_hi == 0x03

    transport.close()

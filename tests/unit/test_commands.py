"""Unit tests for BMS commands."""

import pytest
import struct
from orion1000_bms.commands.read_total_voltage import ReadTotalVoltageRequest, ReadTotalVoltageResponse
from orion1000_bms.commands.read_current import ReadCurrentRequest, ReadCurrentResponse
from orion1000_bms.commands.read_cell_voltage import ReadCellVoltageRequest, ReadCellVoltageResponse
from orion1000_bms.commands.registry import CommandId, COMMANDS


@pytest.mark.phase5
def test_read_total_voltage_request() -> None:
    """Test read total voltage request."""
    req = ReadTotalVoltageRequest()
    assert req.command_id == CommandId.READ_TOTAL_VOLTAGE
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_read_total_voltage_response() -> None:
    """Test read total voltage response parsing."""
    # Test voltage 48.5V = 485 (0x01E5)
    payload = struct.pack(">H", 485)
    resp = ReadTotalVoltageResponse.from_payload(payload)
    assert resp.voltage == 48.5


@pytest.mark.phase5
def test_read_total_voltage_response_invalid_length() -> None:
    """Test read total voltage response with invalid payload length."""
    with pytest.raises(ValueError, match="Invalid payload length"):
        ReadTotalVoltageResponse.from_payload(b"\x01")


@pytest.mark.phase5
def test_read_current_request() -> None:
    """Test read current request."""
    req = ReadCurrentRequest()
    assert req.command_id == CommandId.READ_CURRENT
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_read_current_response() -> None:
    """Test read current response parsing."""
    # Test current 10.5A = 105 (0x0069)
    payload = struct.pack(">H", 105)
    resp = ReadCurrentResponse.from_payload(payload)
    assert resp.current == 10.5


@pytest.mark.phase5
def test_read_current_response_invalid_length() -> None:
    """Test read current response with invalid payload length."""
    with pytest.raises(ValueError, match="Invalid payload length"):
        ReadCurrentResponse.from_payload(b"\x01\x02\x03")


@pytest.mark.phase5
def test_read_cell_voltage_request() -> None:
    """Test read cell voltage request."""
    req = ReadCellVoltageRequest(cell_index=5)
    assert req.command_id == CommandId.READ_CELL_VOLTAGE
    assert req.address == 0x01
    assert req.cell_index == 5
    assert req.to_payload() == b"\x05"


@pytest.mark.phase5
def test_read_cell_voltage_response() -> None:
    """Test read cell voltage response parsing."""
    # Test cell 3, voltage 3.456V = 3456 (0x0D80)
    payload = b"\x03" + struct.pack(">H", 3456)
    resp = ReadCellVoltageResponse.from_payload(payload)
    assert resp.cell_index == 3
    assert resp.voltage == 3.456


@pytest.mark.phase5
def test_read_cell_voltage_response_invalid_length() -> None:
    """Test read cell voltage response with invalid payload length."""
    with pytest.raises(ValueError, match="Invalid payload length"):
        ReadCellVoltageResponse.from_payload(b"\x01\x02")


@pytest.mark.phase5
def test_command_registry() -> None:
    """Test command registry contains all commands."""
    assert CommandId.READ_TOTAL_VOLTAGE in COMMANDS
    assert CommandId.READ_CURRENT in COMMANDS
    assert CommandId.READ_CELL_VOLTAGE in COMMANDS
    
    # Test command specs
    total_voltage_spec = COMMANDS[CommandId.READ_TOTAL_VOLTAGE]
    assert total_voltage_spec.req == ReadTotalVoltageRequest
    assert total_voltage_spec.resp == ReadTotalVoltageResponse
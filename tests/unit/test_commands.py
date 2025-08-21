"""Unit tests for BMS commands."""

import pytest
import struct
from orion1000_bms.commands import (
    VoltageRequest,
    VoltageResponse,
    CurrentStatusRequest,
    CurrentStatusResponse,
    CapacityStatusRequest,
    CapacityStatusResponse,
    SerialNumberRequest,
    SerialNumberResponse,
    AllowDischargeRequest,
    MosControlResponse,
    CommandId,
    COMMANDS,
)


@pytest.mark.phase5
def test_voltage_request() -> None:
    """Test voltage request."""
    req = VoltageRequest()
    assert req.command_id == CommandId.VOLTAGE_REQUEST
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_voltage_response() -> None:
    """Test voltage response parsing."""
    # Create test payload: cmd_hi + cmd_lo + 16 cell voltages + 3 temperatures + string count
    payload = bytearray([0xFF, 0x02])  # Command bytes
    
    # Add 16 cell voltages (3000-3015 mV)
    for i in range(16):
        voltage_mv = 3000 + i
        payload.extend(struct.pack(">H", voltage_mv))
    
    # Add 3 temperatures (25.0, 26.5, 24.8 °C)
    payload.extend(struct.pack(">h", 250))  # 25.0°C
    payload.extend(struct.pack(">h", 265))  # 26.5°C
    payload.extend(struct.pack(">h", 248))  # 24.8°C
    
    # Add string count
    payload.append(2)
    
    resp = VoltageResponse.from_payload(bytes(payload))
    assert len(resp.cell_voltages) == 16
    assert resp.cell_voltages[0] == 3.000
    assert resp.cell_voltages[15] == 3.015
    assert len(resp.temperatures) == 3
    assert resp.temperatures[0] == 25.0
    assert resp.temperatures[1] == 26.5
    assert resp.temperatures[2] == 24.8
    assert resp.system_string_count == 2


@pytest.mark.phase5
def test_voltage_response_invalid_length() -> None:
    """Test voltage response with invalid payload length."""
    with pytest.raises(ValueError, match="Invalid payload length"):
        VoltageResponse.from_payload(b"\x01")


@pytest.mark.phase5
def test_current_status_request() -> None:
    """Test current status request."""
    req = CurrentStatusRequest()
    assert req.command_id == CommandId.CURRENT_STATUS_REQUEST
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_current_status_response() -> None:
    """Test current status response parsing."""
    # Create test payload: cmd_hi + cmd_lo + status + current + protection + 3 temps + mos + version + faults
    payload = bytearray([0xFF, 0x03])  # Command bytes
    payload.append(0x01)  # Status bits
    payload.extend(struct.pack(">h", 105))  # Current 10.5A
    payload.append(0x00)  # Protection status
    payload.extend(struct.pack(">h", 250))  # Temp 1: 25.0°C
    payload.extend(struct.pack(">h", 265))  # Temp 2: 26.5°C
    payload.extend(struct.pack(">h", 248))  # Temp 3: 24.8°C
    payload.append(0x03)  # MOS states
    payload.append(0x01)  # Version
    payload.append(0x00)  # Fault flags
    
    resp = CurrentStatusResponse.from_payload(bytes(payload))
    assert resp.status_bits == 0x01
    assert resp.current == 10.5
    assert resp.protection_status == 0x00
    assert len(resp.temperatures) == 3
    assert resp.temperatures[0] == 25.0
    assert resp.mos_states == 0x03
    assert resp.version == 0x01
    assert resp.fault_flags == 0x00


@pytest.mark.phase5
def test_current_status_response_invalid_length() -> None:
    """Test current status response with invalid payload length."""
    with pytest.raises(ValueError, match="Invalid payload length"):
        CurrentStatusResponse.from_payload(b"\x01\x02\x03")


@pytest.mark.phase5
def test_serial_number_request() -> None:
    """Test serial number request."""
    req = SerialNumberRequest()
    assert req.command_id == CommandId.SERIAL_NUMBER_REQUEST
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_serial_number_response() -> None:
    """Test serial number response parsing."""
    # Create test payload: cmd_hi + cmd_lo + length + ASCII data
    test_serial = "BMS123456"
    payload = bytearray([0xFF, 0x11])  # Command bytes
    payload.append(len(test_serial))  # Length
    payload.extend(test_serial.encode('ascii'))  # ASCII data
    
    resp = SerialNumberResponse.from_payload(bytes(payload))
    assert resp.serial_number == test_serial


@pytest.mark.phase5
def test_mos_control_request() -> None:
    """Test MOS control request."""
    req = AllowDischargeRequest()
    assert req.command_id == CommandId.ALLOW_DISCHARGE
    assert req.address == 0x01
    assert req.to_payload() == b""


@pytest.mark.phase5
def test_mos_control_response() -> None:
    """Test MOS control response parsing."""
    # Create test payload: cmd_hi + cmd_lo + status
    payload = bytes([0xFF, 0x19, 0x00])  # Command echo + success status
    
    resp = MosControlResponse.from_payload(payload)
    assert resp.command_id == 0x19
    assert resp.status == 0x00
    assert resp.success is True


@pytest.mark.phase5
def test_command_registry() -> None:
    """Test command registry contains all commands."""
    assert CommandId.VOLTAGE_REQUEST in COMMANDS
    assert CommandId.CURRENT_STATUS_REQUEST in COMMANDS
    assert CommandId.CAPACITY_STATUS_REQUEST in COMMANDS
    assert CommandId.SERIAL_NUMBER_REQUEST in COMMANDS
    assert CommandId.ALLOW_DISCHARGE in COMMANDS
    
    # Test command specs
    voltage_spec = COMMANDS[CommandId.VOLTAGE_REQUEST]
    assert voltage_spec.req == VoltageRequest
    assert voltage_spec.resp == VoltageResponse
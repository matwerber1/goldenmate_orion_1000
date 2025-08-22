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
    # Create test payload: cmd_hi + cmd_lo + cell_count + temp_probes + total_cells + cell voltages
    payload = bytearray([0xFF, 0x02])  # Command bytes
    payload.append(4)  # 4 cells in packet
    payload.append(3)  # 3 temp probes
    payload.append(4)  # 4 total system cells
    
    # Add 4 cell voltages (3000-3003 mV)
    for i in range(4):
        voltage_mv = 3000 + i
        payload.extend(struct.pack(">H", voltage_mv))
    
    resp = VoltageResponse.from_payload(bytes(payload))
    assert len(resp.cell_voltages) == 4
    assert resp.cell_voltages[0] == 3.000
    assert resp.cell_voltages[3] == 3.003
    assert resp.cell_count_in_packet == 4
    assert resp.temp_probe_count == 3
    assert resp.total_system_cells == 4


@pytest.mark.phase5
def test_voltage_response_invalid_length() -> None:
    """Test voltage response with invalid payload length."""
    with pytest.raises(ValueError, match="Payload too short"):
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
    # Create test payload matching new protocol specification
    payload = bytearray([0xFF, 0x03])  # Command bytes
    payload.append(0x01)  # Status flags: discharge_active=1
    payload.extend(struct.pack(">H", 1050))  # Current 1050 * 10mA = 10.5A
    payload.append(0x00)  # OV protection
    payload.append(0x00)  # UV protection
    payload.append(0x00)  # Temp protection
    payload.append(0x00)  # General protection
    payload.append(3)     # 3 temperature probes
    payload.append(65)    # Temp 1: 65 - 40 = 25°C
    payload.append(66)    # Temp 2: 66 - 40 = 26°C
    payload.append(64)    # Temp 3: 64 - 40 = 24°C
    payload.append(0x01)  # Software version
    payload.append(0x03)  # MOS states
    payload.append(0x00)  # Failure status
    
    resp = CurrentStatusResponse.from_payload(bytes(payload))
    assert resp.status_flags["discharge_active"] is True
    assert resp.current == 10.5
    assert resp.temp_probe_count == 3
    assert len(resp.temperatures) == 3
    assert resp.temperatures[0] == 25.0
    assert resp.temperatures[1] == 26.0
    assert resp.temperatures[2] == 24.0
    assert resp.software_version == 0x01


@pytest.mark.phase5
def test_current_status_response_invalid_length() -> None:
    """Test current status response with invalid payload length."""
    with pytest.raises(ValueError, match="Payload too short"):
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
    # Create test payload: cmd_hi + cmd_lo (fixed acknowledgment format)
    payload = bytes([0xFF, 0xFF])  # Fixed acknowledgment
    
    resp = MosControlResponse.from_payload(payload)
    assert resp.command_id == 0xFF
    assert resp.status == 0x00  # Success
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
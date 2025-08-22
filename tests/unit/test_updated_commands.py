"""Tests for updated command parsing logic."""

import pytest
from orion1000_bms.commands.voltage_request import VoltageResponse
from orion1000_bms.commands.current_status_request import CurrentStatusResponse
from orion1000_bms.commands.capacity_status_request import CapacityStatusResponse
from orion1000_bms.commands.mos_control import MosControlResponse


class TestVoltageResponse:
    """Test voltage response parsing with new protocol."""

    def test_parse_4_cell_voltage_response(self) -> None:
        """Test parsing 4-cell voltage response."""
        # Payload: cmd_hi(FF) + cmd_lo(02) + cell_count(04) + temp_probes(03) + total_cells(04) + 4 voltages
        payload = (
            b"\xff\x02"  # Command bytes
            + b"\x04"  # 4 cells in packet
            + b"\x03"  # 3 temp probes
            + b"\x04"  # 4 total system cells
            + b"\x0f\xa0"  # Cell 1: 4000mV = 4.0V
            + b"\x0f\x96"  # Cell 2: 3990mV = 3.99V
            + b"\x0f\x8c"  # Cell 3: 3980mV = 3.98V
            + b"\x0f\x82"  # Cell 4: 3970mV = 3.97V
        )

        response = VoltageResponse.from_payload(payload)

        assert response.cell_count_in_packet == 4
        assert response.temp_probe_count == 3
        assert response.total_system_cells == 4
        assert len(response.cell_voltages) == 4
        assert response.cell_voltages[0] == 4.0
        assert response.cell_voltages[1] == 3.99
        assert response.cell_voltages[2] == 3.98
        assert response.cell_voltages[3] == 3.97

    def test_parse_insufficient_data(self) -> None:
        """Test error handling for insufficient data."""
        payload = b"\xff\x02\x04\x03\x04\x0f"  # Missing voltage data

        with pytest.raises(ValueError, match="Insufficient data"):
            VoltageResponse.from_payload(payload)


class TestCurrentStatusResponse:
    """Test current status response parsing with new protocol."""

    def test_parse_current_status_response(self) -> None:
        """Test parsing current status response."""
        payload = (
            b"\xff\x03"  # Command bytes
            + b"\x03"  # Status flags: discharge_active=1, charge_active=1
            + b"\x03\xe8"  # Current: 1000 * 10mA = 10A
            + b"\x11"  # OV protection: cell_ov=1 (bit0), full_charge_protection=1 (bit4)
            + b"\x03"  # UV protection: cell_uv=1, pack_uv=1
            + b"\x07"  # Temp protection: charge_temp=1, discharge_temp=1, mos_over_temp=1
            + b"\x33"  # General protection: discharge_short_circuit=1, charge_oc=1, ambient_high_temp=1, ambient_low_temp=1
            + b"\x03"  # 3 temperature probes
            + b"\x50"  # Temp 1: 80 - 40 = 40°C
            + b"\x46"  # Temp 2: 70 - 40 = 30°C
            + b"\x3c"  # Temp 3: 60 - 40 = 20°C
            + b"\x01"  # Software version
            + b"\x06"  # MOS state: discharge_mos_on=1, charge_mos_on=1
            + b"\x0f"  # Failure status: all failures
        )

        response = CurrentStatusResponse.from_payload(payload)

        assert response.status_flags["discharge_active"] is True
        assert response.status_flags["charge_active"] is True
        assert response.current == 10.0
        assert response.overvoltage_protection["cell_ov"] is True
        assert response.overvoltage_protection["full_charge_protection"] is True
        assert response.undervoltage_protection["cell_uv"] is True
        assert response.undervoltage_protection["pack_uv"] is True
        assert response.temp_probe_count == 3
        assert len(response.temperatures) == 3
        assert response.temperatures[0] == 40.0
        assert response.temperatures[1] == 30.0
        assert response.temperatures[2] == 20.0
        assert response.software_version == 1
        assert response.mos_state["discharge_mos_on"] is True
        assert response.mos_state["charge_mos_on"] is True


class TestCapacityStatusResponse:
    """Test capacity status response parsing with new protocol."""

    def test_parse_capacity_status_response(self) -> None:
        """Test parsing capacity status response with tagged data."""
        # Create minimal valid payload for testing
        payload = (
            b"\xff\x04"  # Command bytes
            + b"\x01\x64"  # Tag 0x01: SOC = 100%
            + b"\x02\x00\x64"  # Tag 0x02: Cycle count = 100
            + b"\x00" * 45  # Padding to meet minimum length requirement
        )

        response = CapacityStatusResponse.from_payload(payload)

        # Verify basic tagged data parsing works
        assert response.soc == 100
        assert response.cycle_count == 100


class TestMosControlResponse:
    """Test MOS control response parsing with new protocol."""

    def test_parse_mos_control_response(self) -> None:
        """Test parsing MOS control acknowledgment response."""
        payload = b"\xff\xff"  # Fixed acknowledgment format

        response = MosControlResponse.from_payload(payload)

        assert response.command_id == 0xFF
        assert response.status == 0x00  # Success
        assert response.success is True

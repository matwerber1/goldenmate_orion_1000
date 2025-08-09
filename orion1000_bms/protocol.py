from __future__ import annotations
import logging

log = logging.getLogger(__name__)

"""
Orion 1000 BMS Protocol (GoldenMate) — Python 3.13-ready reference module

This module provides strongly typed builders and parsers for the proprietary
serial frames used by the Orion1000 BMS seen in the "BMS Communication
Protocol Technical Specification" (doc: JGDY/C-RE&RD-PK20, R1.2, 2022-07-01).

Interfaces covered: UART/RS485/RS232 framing (0xEA ... 0xF5). CAN tunneling
uses the same frame bytes at the payload level, so you can reuse these helpers
with your own CAN transport.
"""

from dataclasses import dataclass, field
from enum import Enum, IntFlag
from typing import Final, Iterable, List, Tuple, Sequence, TypeAlias, Optional


def hexdump(b: bytes) -> str:
    return " ".join(f"{x:02X}" for x in b)


def be16(hi: int, lo: int) -> int:
    return (hi << 8) | lo


def le16(lo: int, hi: int) -> int:
    return (hi << 8) | lo


def xor_checksum(data: bytes, start: int, end: int) -> int:
    c = 0
    for x in data[start : end + 1]:
        c ^= x
    return c


@dataclass
class CurrentStatusDiagnostics:
    length_field: int
    actual_len: int
    length_ok: bool
    checksum_ok: bool
    cmd: tuple[int, int]
    status_byte: int
    discharge_active: bool
    charge_active: bool
    mos_temp_present: bool
    ambient_temp_present: bool
    raw_current_10ma_be: int
    raw_current_10ma_le: int
    chosen_endianness: str
    current_ma_unsigned: int
    current_a_signed: float
    warnings: list[str]


class ProtocolError(RuntimeError):
    pass


START_BYTE: Final[int] = 0xEA
PRODUCT_ID: Final[int] = 0xD1
END_BYTE: Final[int] = 0xF5

DEFAULT_ADDR: Final[int] = 0x01
SERIAL_BAUD: Final[int] = 9600  # 8N1


class Command(Enum):
    """Low-byte command values under the fixed high-byte 0xFF."""

    VOLTAGE_REQUEST = 0x02
    CURRENT_STATUS_REQUEST = 0x03
    CAPACITY_STATUS_REQUEST = 0x04
    BATTERY_ID_REQUEST = 0x11
    ALLOW_DISCHARGE = 0x19
    DISABLE_DISCHARGE = 0x1A
    ALLOW_CHARGE = 0x1B
    DISABLE_CHARGE = 0x1C
    ACK = 0xFF  # reply low-byte when high-byte is also 0xFF


@dataclass(slots=True, frozen=True)
class AckData:
    address: int

    @classmethod
    def from_bytes(cls, frame: bytes) -> "AckData":
        _validate_preamble(frame)
        _validate_length_field(frame)
        _expect_cmd(frame, Command.ACK)
        _validate_reply_checksum(frame)
        return cls(address=frame[2])


def _xor_checksum(data: bytes) -> int:
    x = 0
    for b in data:
        x ^= b
    return x & 0xFF


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def build_command(cmd: Command, addr: int = DEFAULT_ADDR) -> bytes:
    _require(0 <= addr <= 0xFF, "address must fit in one byte")
    length = 0x04
    cmd_hi = 0xFF
    cmd_lo = cmd.value
    xor = _xor_checksum(bytes((length, cmd_hi, cmd_lo)))
    return bytes((START_BYTE, PRODUCT_ID, addr, length, cmd_hi, cmd_lo, xor, END_BYTE))


def _validate_preamble(frame: bytes) -> None:
    _require(len(frame) >= 8, "frame too short")
    _require(frame[0] == START_BYTE, "bad start byte")
    _require(frame[1] == PRODUCT_ID, "bad product id")
    _require(frame[-1] == END_BYTE, "missing end byte")


def _validate_length_field(frame: bytes) -> None:
    reported = frame[3]
    expected_total = 4 + reported
    _require(
        len(frame) == expected_total,
        f"length mismatch: reported {reported} => total {expected_total}, got {len(frame)}",
    )


def _validate_reply_checksum(frame: bytes) -> None:
    xor_span = frame[3:-2]
    xor_reported = frame[-2]
    xor_calc = _xor_checksum(xor_span)

    log.debug(
        "Checksum debug: span=%s  calc=0x%02X  reported=0x%02X",
        " ".join(f"{b:02X}" for b in xor_span),
        xor_calc,
        xor_reported,
    )

    _require(
        xor_reported == xor_calc,
        f"checksum mismatch: got 0x{xor_reported:02X}, expected 0x{xor_calc:02X}",
    )


def _expect_cmd(frame: bytes, cmd: Command) -> None:
    _require(
        frame[4] == 0xFF and frame[5] == cmd.value,
        f"unexpected command in reply: 0x{frame[4]:02X} 0x{frame[5]:02X}",
    )


@dataclass(slots=True, frozen=True)
class VoltageData:
    address: int
    series_cells_in_packet: int
    probe_count: int
    system_series_cells: int
    cell_mv: Tuple[int, ...]

    @property
    def cell_count(self) -> int:
        return len(self.cell_mv)

    def min_max_mv(self) -> tuple[int, int]:
        return (min(self.cell_mv), max(self.cell_mv))

    @classmethod
    def from_bytes(cls, frame: bytes) -> "VoltageData":
        _validate_preamble(frame)
        _validate_length_field(frame)
        _expect_cmd(frame, Command.VOLTAGE_REQUEST)
        _validate_reply_checksum(frame)

        addr = frame[2]
        series_cells = frame[6]
        probe_count = frame[7]
        system_series = frame[8]

        payload = frame[9:-2]
        _require(len(payload) % 2 == 0, "cell payload not 2-byte aligned")
        values = []
        for i in range(0, len(payload), 2):
            mv = (payload[i] << 8) | payload[i + 1]
            values.append(mv)

        return cls(
            address=addr,
            series_cells_in_packet=series_cells,
            probe_count=probe_count,
            system_series_cells=system_series,
            cell_mv=tuple(values),
        )


class StatusBits(IntFlag):
    DISCHARGING_PRESENT = 1 << 0
    CHARGING_PRESENT = 1 << 1
    HAS_MOS_TEMP = 1 << 4
    HAS_AMBIENT_TEMP = 1 << 5


class OverVoltageBits(IntFlag):
    CELL_OVP = 1 << 0
    PACK_OVP = 1 << 1
    FULL_CHARGE_PROTECT = 1 << 4


class UnderVoltageBits(IntFlag):
    CELL_UVP = 1 << 0
    PACK_UVP = 1 << 1


class TempProtectBits(IntFlag):
    CHARGE_TEMP_PROTECT = 1 << 0
    DISCHARGE_TEMP_PROTECT = 1 << 1
    MOS_OVER_TEMP = 1 << 2
    HIGH_TEMP_PROTECT = 1 << 4
    LOW_TEMP_PROTECT = 1 << 5


class ProtectBits(IntFlag):
    DISCHARGE_SHORT = 1 << 0
    DISCHARGE_OC = 1 << 1
    CHARGE_OC = 1 << 2
    AMBIENT_HIGH_TEMP = 1 << 4
    AMBIENT_LOW_TEMP = 1 << 5


class MosStateBits(IntFlag):
    DISCHARGE_MOS_ON = 1 << 1
    CHARGE_MOS_ON = 1 << 2


class FaultBits(IntFlag):
    TEMP_ACQ_FAIL = 1 << 0
    VOLT_ACQ_FAIL = 1 << 1
    DISCHARGE_MOS_FAIL = 1 << 2
    CHARGE_MOS_FAIL = 1 << 3


@dataclass(slots=True, frozen=True)
class CurrentStatusData:
    address: int
    # Raw aggregated status bits from byte 7
    status: StatusBits
    # New convenience booleans derived from `status` bits
    discharge_active: bool
    charge_active: bool
    mos_temp_present: bool
    ambient_temp_present: bool

    current_ma: int
    over_voltage: OverVoltageBits
    under_voltage: UnderVoltageBits
    temp_protect: TempProtectBits
    protect: ProtectBits
    probe_count: int
    cell_temps_c: Tuple[int, ...]
    mos_temp_c: Optional[int]
    ambient_temp_c: Optional[int]
    sw_version: int
    mos_state: MosStateBits
    faults: FaultBits

    @classmethod
    def from_bytes(cls, frame: bytes) -> "CurrentStatusData":
        _validate_preamble(frame)
        _validate_length_field(frame)
        _expect_cmd(frame, Command.CURRENT_STATUS_REQUEST)
        _validate_reply_checksum(frame)

        addr = frame[2]
        status = StatusBits(frame[6])

        # Derive per-bit convenience booleans
        discharge_active = bool(status & StatusBits.DISCHARGING_PRESENT)
        charge_active = bool(status & StatusBits.CHARGING_PRESENT)
        mos_temp_present = bool(status & StatusBits.HAS_MOS_TEMP)
        ambient_temp_present = bool(status & StatusBits.HAS_AMBIENT_TEMP)

        # Current reported in 10 mA units. Despite the PDF describing [8]=high,[9]=low,
        # real-world frames from Orion1000 appear LITTLE-ENDIAN (low, high). Using LE fixes
        # absurdly large readings (e.g., ~200 A when the actual load is ~0.8 A).
        current_10ma = frame[8] | (frame[9] << 8)
        current_ma = current_10ma * 10

        ov = OverVoltageBits(frame[10])
        uv = UnderVoltageBits(frame[11])
        tp = TempProtectBits(frame[12])
        prot = ProtectBits(frame[13])

        # --- Temperature / probe block ---
        # Some firmware revisions omit the explicit probe-count byte documented in the
        # PDF and instead begin temperature bytes immediately at index 14. To be
        # robust, derive the layout from the total frame length.
        has_mos = mos_temp_present
        has_amb = ambient_temp_present
        tail_sensors = (1 if has_mos else 0) + (1 if has_amb else 0)

        # Fixed trailer after temperature bytes (before checksum & end):
        # 5 bytes reserved + 1 sw_version + 1 mos_state + 1 faults + 2 bytes reserved = 10
        # Plus checksum & end = 2 more (handled by total length below)
        fixed_trailer_no_ce = 10

        # Index right after the last temperature-related byte
        idx_after_temps = len(frame) - (fixed_trailer_no_ce + 2)

        # Try the documented layout first: byte 14 is probe count, temps start at 15
        explicit_count = frame[14]
        # Explicit-count layout: temps start at index 14 and there are N temperature bytes.
        uses_explicit = (14 + explicit_count) == idx_after_temps

        if uses_explicit:
            n_probes = explicit_count
            idx = 15
        else:
            # Implicit layout: temps start at 14 and run up to idx_after_temps
            n_probes = idx_after_temps - 14
            idx = 14
            if n_probes < 0:
                raise ValueError("bad current-status layout: negative probe count")
            # Optional: help debugging in logs
            log.debug(
                "Implicit probe-count layout used: n_probes=%d (derived)", n_probes
            )

        # Split probe bytes into cell temps and tail sensors
        x_cell = max(0, n_probes - tail_sensors)

        cell_temps_c: list[int] = []
        for _ in range(x_cell):
            cell_temps_c.append(frame[idx] - 40)
            idx += 1

        mos_temp_c: Optional[int] = None
        if has_mos and (n_probes - x_cell) > 0:
            mos_temp_c = frame[idx] - 40
            idx += 1

        ambient_temp_c: Optional[int] = None
        if has_amb and (n_probes - x_cell - (1 if has_mos else 0)) > 0:
            ambient_temp_c = frame[idx] - 40
            idx += 1

        # 5 bytes reserved
        idx += 5

        sw_version = frame[idx]
        idx += 1
        mos_state = MosStateBits(frame[idx])
        idx += 1
        faults = FaultBits(frame[idx])
        idx += 1

        return cls(
            address=addr,
            status=status,
            discharge_active=discharge_active,
            charge_active=charge_active,
            mos_temp_present=mos_temp_present,
            ambient_temp_present=ambient_temp_present,
            current_ma=current_ma,
            over_voltage=ov,
            under_voltage=uv,
            temp_protect=tp,
            protect=prot,
            probe_count=n_probes,
            cell_temps_c=tuple(cell_temps_c),
            mos_temp_c=mos_temp_c,
            ambient_temp_c=ambient_temp_c,
            sw_version=sw_version,
            mos_state=mos_state,
            faults=faults,
        )


@dataclass(slots=True, frozen=True)
class CapacityData:
    address: int
    soc_percent: int
    cycles: int
    design_capacity_mah: int
    full_capacity_mah: int
    remaining_capacity_mah: int
    remaining_discharge_min: int
    remaining_charge_min: int
    current_charge_interval_h: int
    longest_charge_interval_h: int
    pack_voltage_mv: int
    highest_cell_mv: int
    lowest_cell_mv: int
    hw_version: int
    scheme_high_nibble: int
    scheme_low_nibble: int

    @classmethod
    def from_bytes(cls, frame: bytes) -> "CapacityData":
        _validate_preamble(frame)
        _validate_length_field(frame)
        _expect_cmd(frame, Command.CAPACITY_STATUS_REQUEST)
        _validate_reply_checksum(frame)

        addr = frame[2]

        _require(frame[6] == 0x01, "marker 0x01 missing")
        soc = frame[7]

        _require(frame[8] == 0x02, "marker 0x02 missing")
        cycles = (frame[9] << 8) | frame[10]

        _require(frame[11] == 0x03, "marker 0x03 missing")
        design_hi2 = (frame[12] << 8) | frame[13]
        _require(frame[14] == 0x04, "marker 0x04 missing")
        design_lo2 = (frame[15] << 8) | frame[16]
        design_capacity_mah = (design_hi2 << 16) | design_lo2

        _require(frame[17] == 0x05, "marker 0x05 missing")
        full_hi2 = (frame[18] << 8) | frame[19]
        _require(frame[20] == 0x06, "marker 0x06 missing")
        full_lo2 = (frame[21] << 8) | frame[22]
        full_capacity_mah = (full_hi2 << 16) | full_lo2

        _require(frame[23] == 0x07, "marker 0x07 missing")
        rem_hi2 = (frame[24] << 8) | frame[25]
        _require(frame[26] == 0x08, "marker 0x08 missing")
        rem_lo2 = (frame[27] << 8) | frame[28]
        remaining_capacity_mah = (rem_hi2 << 16) | rem_lo2

        _require(frame[29] == 0x09, "marker 0x09 missing")
        rem_discharge_min = (frame[30] << 8) | frame[31]

        _require(frame[32] == 0x0A, "marker 0x0A missing")
        rem_charge_min = (frame[33] << 8) | frame[34]

        _require(frame[35] == 0x0B, "marker 0x0B missing")
        current_charge_h = (frame[36] << 8) | frame[37]
        longest_charge_h = (frame[38] << 8) | frame[39]

        pack_v_10mv = (frame[47] << 8) | frame[48]
        pack_mv = pack_v_10mv * 10

        highest_mv = (frame[49] << 8) | frame[50]
        lowest_mv = (frame[51] << 8) | frame[52]

        _require(frame[53] == 0x0D, "marker 0x0D missing")
        hw = frame[54]
        scheme = frame[55]
        scheme_high = (scheme >> 4) & 0x0F
        scheme_low = scheme & 0x0F

        return cls(
            address=addr,
            soc_percent=soc,
            cycles=cycles,
            design_capacity_mah=design_capacity_mah,
            full_capacity_mah=full_capacity_mah,
            remaining_capacity_mah=remaining_capacity_mah,
            remaining_discharge_min=rem_discharge_min,
            remaining_charge_min=rem_charge_min,
            current_charge_interval_h=current_charge_h,
            longest_charge_interval_h=longest_charge_h,
            pack_voltage_mv=pack_mv,
            highest_cell_mv=highest_mv,
            lowest_cell_mv=lowest_mv,
            hw_version=hw,
            scheme_high_nibble=scheme_high,
            scheme_low_nibble=scheme_low,
        )


@dataclass(slots=True, frozen=True)
class BatteryIdData:
    address: int
    id_ascii: str

    @classmethod
    def from_bytes(cls, frame: bytes) -> "BatteryIdData":
        _validate_preamble(frame)
        _validate_length_field(frame)
        _expect_cmd(frame, Command.BATTERY_ID_REQUEST)
        _validate_reply_checksum(frame)

        addr = frame[2]
        length = frame[6]
        id_bytes = frame[7 : 7 + length]
        return cls(address=addr, id_ascii=id_bytes.decode("ascii", errors="replace"))


def build_mos_control_allow_discharge(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.ALLOW_DISCHARGE, addr)


def build_mos_control_disable_discharge(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.DISABLE_DISCHARGE, addr)


def build_mos_control_allow_charge(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.ALLOW_CHARGE, addr)


def build_mos_control_disable_charge(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.DISABLE_CHARGE, addr)


_SAMPLE_VOLTAGE_REPLY_HEX = (
    "EA D1 01 27 FF 02 0F 06 0F 0B 4E 0E 9C 0E 5F 0E 84 0E A0 0E A5 0E 8F 0E A0 "
    "0E A0 0E 8B 0E B0 0E 92 0E 7D 0E B6 0E 73 0E 73 38 F5"
)


def _hexstr_to_bytes(s: str) -> bytes:
    return bytes(int(b, 16) for b in s.split())


def self_test() -> None:
    frame = _hexstr_to_bytes(_SAMPLE_VOLTAGE_REPLY_HEX)
    vd = VoltageData.from_bytes(frame)
    assert vd.address == 0x01
    assert vd.cell_count == len(vd.cell_mv)
    _ = vd.min_max_mv()


def build_voltage_request(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.VOLTAGE_REQUEST, addr)


def build_current_status_request(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.CURRENT_STATUS_REQUEST, addr)


def build_capacity_status_request(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.CAPACITY_STATUS_REQUEST, addr)


def build_battery_id_request(addr: int = DEFAULT_ADDR) -> bytes:
    return build_command(Command.BATTERY_ID_REQUEST, addr)


__all__ = [
    "AckData",
    "START_BYTE",
    "PRODUCT_ID",
    "END_BYTE",
    "DEFAULT_ADDR",
    "SERIAL_BAUD",
    "Command",
    "VoltageData",
    "CurrentStatusData",
    "CapacityData",
    "BatteryIdData",
    "StatusBits",
    "OverVoltageBits",
    "UnderVoltageBits",
    "TempProtectBits",
    "ProtectBits",
    "MosStateBits",
    "FaultBits",
    "build_voltage_request",
    "build_current_status_request",
    "build_capacity_status_request",
    "build_battery_id_request",
    "build_mos_control_allow_discharge",
    "build_mos_control_disable_discharge",
    "build_mos_control_allow_charge",
    "build_mos_control_disable_charge",
    "self_test",
]

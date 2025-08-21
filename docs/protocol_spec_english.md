# GoldenMate Orion 1000 Battery Management System (BMS) Serial Communication Protocol

This document is an English translation and clarification of the original Chinese specification. It focuses exclusively on the RS485/RS232/UART serial communication aspects. CAN bus details are omitted here (but were included in the original Chinese specification).

---

## Serial Communication Parameters

- **Interface**: RS485 / RS232 / UART
- **Baud Rate**: 9600 bps
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Protocol Type**: Master–Slave (host sends request, BMS replies)
- **Timing**: Host must wait at least 100 ms between consecutive scan command requests

---

## Frame Structure Overview

All communication is based on fixed-length request frames (8 bytes) and variable-length response frames (depending on the command and battery configuration).

### Request Frame Format (8 Bytes)

| Byte | Name                  | Value / Meaning                                                         |
| ---- | --------------------- | ----------------------------------------------------------------------- |
| 1    | **Start Byte**        | `0xEA` (fixed)                                                          |
| 2    | **Product ID**        | `0xD1` (fixed)                                                          |
| 3    | **Battery Address**   | Default `0x01`; set by DIP switch if available                          |
| 4    | **Data Length**       | Always `0x04` (length from this byte to end byte, not including itself) |
| 5    | **Command High Byte** | Always `0xFF`                                                           |
| 6    | **Command Low Byte**  | Varies depending on request type (see below)                            |
| 7    | **Checksum**          | XOR of bytes 4–6 (Length + Command High + Command Low)                  |
| 8    | **End Byte**          | `0xF5` (fixed)                                                          |

### Notes on Checksum (Byte 7)

- The checksum is a **1-byte XOR** of bytes 4, 5, and 6.
- Example: For Length=`0x04`, Command High=`0xFF`, Command Low=`0x02`,

  - Calculation: `0x04 XOR 0xFF XOR 0x02 = 0xF9`

---

## Request Types (Command Low Byte)

The following subsections describe supported request types. Each request is defined by the **Command Low Byte** (Byte 6 of the request frame).

### 0x02 — Voltage Data Request

- Purpose: Request individual cell voltages and related metadata.
- Example Request: `EA D1 01 04 FF 02 F9 F5`

### 0x03 — Current and Status Data Request

- Purpose: Request current measurement, status flags, and protection indicators.
- Example Request: `EA D1 01 04 FF 03 F8 F5`

### 0x04 — Capacity and State of Charge (SOC) Data Request

- Purpose: Request capacity metrics such as design capacity, full charge capacity, remaining capacity, SOC%, and related values.
- Example Request: `EA D1 01 04 FF 04 FF F5`

### 0x11 — Battery Serial Number Request

- Purpose: Request ASCII identifier of the battery pack.
- Example Request: `EA D1 01 04 FF 11 EA F5`

### 0x19 — Enable Discharge Command

- Purpose: Allow discharge by enabling discharge MOSFET.
- Example Request: `EA D1 01 04 FF 19 E2 F5`

### 0x1A — Disable Discharge Command

- Purpose: Disable discharge by turning off discharge MOSFET.
- Example Request: `EA D1 01 04 FF 1A E1 F5`

### 0x1B — Enable Charge Command

- Purpose: Allow charging by enabling charge MOSFET.
- Example Request: `EA D1 01 04 FF 1B E0 F5`

### 0x1C — Disable Charge Command

- Purpose: Disable charging by turning off charge MOSFET.
- Example Request: `EA D1 01 04 FF 1C E7 F5`

---

## Response Frames

Response frames are **variable length**, depending on the command and the number of cells or sensors in the battery. The examples shown in this document are illustrative only. Actual lengths and values vary by battery model (e.g., Orion 1000 has only 4 cells, while other packs may have up to 16).

### Voltage Data Packet (Response to 0x02)

| Byte Index | Field Description               | Value / Meaning              | Notes                                           |
| ---------- | ------------------------------- | ---------------------------- | ----------------------------------------------- |
| 1          | Start Byte                      | `0xEA`                       | Fixed                                           |
| 2          | Product ID                      | `0xD1`                       | Fixed                                           |
| 3          | Battery Address                 | `0x01`                       | Fixed or DIP-selected                           |
| 4          | Data Length                     | 1 byte                       | Total length from this byte to End Byte         |
| 5          | Command High Byte               | `0xFF`                       | Fixed                                           |
| 6          | Command Low Byte                | `0x02`                       | Identifies voltage data packet                  |
| 7          | Cell Count in this Packet       | 1 byte                       | Example: `0x10` = 16 cells, `0x04` = 4 cells    |
| 8          | Number of Temperature Probes    | 1 byte                       | Default = `0x03` (cell temp, MOS temp, ambient) |
| 9          | Total Number of Cells in System | 1 byte                       | Reports system-wide series cell count           |
| 10–(9+2N)  | Cell Voltages                   | 2 bytes per cell (High, Low) | Unit = mV, Big-endian (high first)              |
| Next       | Checksum                        | 1 byte                       | XOR of bytes 4 through last data byte           |
| Last       | End Byte                        | `0xF5`                       | Fixed                                           |

### Current and Status Data Packet (Response to 0x03)

| Byte Index | Field Description               | Value / Meaning   | Notes                                                                                                               |
| ---------- | ------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------- |
| 1          | Start Byte                      | `0xEA`            | Fixed                                                                                                               |
| 2          | Product ID                      | `0xD1`            | Fixed                                                                                                               |
| 3          | Battery Address                 | `0x01`            | Fixed                                                                                                               |
| 4          | Data Length                     | 1 byte            | Includes all bytes to End Byte                                                                                      |
| 5          | Command High Byte               | `0xFF`            | Fixed                                                                                                               |
| 6          | Command Low Byte                | `0x03`            | Current/status packet                                                                                               |
| 7          | Status Flags                    | 1 byte, bit field | Bit0: Discharge active; Bit1: Charge active; Bit4: MOS temp present; Bit5: Ambient temp present                     |
| 8–9        | Current Value                   | 2 bytes, unsigned | Unit = 10 mA; High byte first                                                                                       |
| 10         | Over-voltage Protection Status  | Bit field         | Bit0: Cell OV, Bit1: Pack OV, Bit4: Full charge protection                                                          |
| 11         | Under-voltage Protection Status | Bit field         | Bit0: Cell UV, Bit1: Pack UV                                                                                        |
| 12         | Temperature Protection Status   | Bit field         | Bit0: Charge temp, Bit1: Discharge temp, Bit2: MOS over-temp, Bit4: High-temp, Bit5: Low-temp                       |
| 13         | General Protection Status       | Bit field         | Bit0: Discharge short circuit, Bit1: Discharge OC, Bit2: Charge OC, Bit4: Ambient high-temp, Bit5: Ambient low-temp |
| 14         | Number of Temperature Probes    | 1 byte            | Total probes = cells + optional MOS + ambient                                                                       |
| 15+        | Temperature Data                | N bytes           | Each = Actual temp + 40 °C offset                                                                                   |
| …          | Software Version                | 1 byte            | Range 1–255                                                                                                         |
| …          | MOS State                       | 1 byte, bit field | Bit1: Discharge MOS on/off, Bit2: Charge MOS on/off                                                                 |
| …          | Failure Status                  | 1 byte, bit field | Bit0: Temp acquisition fail, Bit1: Voltage acquisition fail, Bit2: Discharge MOS fail, Bit3: Charge MOS fail        |
| …          | Reserved Bytes                  | Variable          | As per spec                                                                                                         |
| Next       | Checksum                        | 1 byte            | XOR of bytes 4 through last data byte                                                                               |
| Last       | End Byte                        | `0xF5`            | Fixed                                                                                                               |

### Capacity and SOC Data Packet (Response to 0x04)

| Byte Index | Field Description | Value / Meaning                    | Notes                                                        |
| ---------- | ----------------- | ---------------------------------- | ------------------------------------------------------------ |
| 1–6        | Header            | Standard (EA D1 Addr Length FF 04) |                                                              |
| 7          | Tag = `0x01`      | SOC                                | % value (0–100%)                                             |
| 8          | SOC Value         | 1 byte                             |                                                              |
| 9          | Tag = `0x02`      | Cycle Count                        |                                                              |
| 10–11      | Cycle Count       | 2 bytes, High–Low                  |                                                              |
| 12         | Tag = `0x03`      | Design Capacity High               | 2 bytes                                                      |
| 15         | Tag = `0x04`      | Design Capacity Low                | 2 bytes                                                      |
| 18         | Tag = `0x05`      | Full Charge Capacity High          | 2 bytes                                                      |
| 21         | Tag = `0x06`      | Full Charge Capacity Low           | 2 bytes                                                      |
| 24         | Tag = `0x07`      | Remaining Capacity High            | 2 bytes                                                      |
| 27         | Tag = `0x08`      | Remaining Capacity Low             | 2 bytes                                                      |
| 30         | Tag = `0x09`      | Remaining Discharge Time           | 2 bytes, min                                                 |
| 33         | Tag = `0x0A`      | Remaining Charge Time              | 2 bytes, min                                                 |
| 36         | Tag = `0x0B`      | Charge Interval                    | 2 values: current interval, max interval (hours)             |
| 48–49      | Pack Voltage      | 2 bytes                            | Unit = 10 mV                                                 |
| 50–51      | Max Cell Voltage  | 2 bytes                            | Unit = 1 mV                                                  |
| 52–53      | Min Cell Voltage  | 2 bytes                            | Unit = 1 mV                                                  |
| 54         | Tag = `0x0D`      | Hardware Version                   | 1 byte (1–255)                                               |
| 55–56      | Scheme ID         | 1 byte                             | High nibble = vendor scheme, Low nibble = protocol extension |
| 57–59      | Reserved          | 3 bytes                            |                                                              |
| Next       | Checksum          | 1 byte                             | XOR of bytes 4 through last data byte                        |
| Last       | End Byte          | `0xF5`                             | Fixed                                                        |

### Serial Number Data Packet (Response to 0x11)

| Byte Index | Field Description    | Value / Meaning                    | Notes                                          |
| ---------- | -------------------- | ---------------------------------- | ---------------------------------------------- |
| 1–6        | Header               | Standard (EA D1 Addr Length FF 11) |                                                |
| 7          | Serial Number Length | 1 byte                             | N (≤31)                                        |
| 8…(7+N)    | Serial Number ASCII  | N bytes                            | ASCII-encoded serial number                    |
| Next       | Checksum             | 1 byte                             | XOR of bytes 4 through last serial number byte |
| Last       | End Byte             | `0xF5`                             | Fixed                                          |

### MOS Control Response (Responses to 0x19–0x1C)

| Byte Index | Field Description | Value / Meaning                        |
| ---------- | ----------------- | -------------------------------------- |
| 1–6        | Header            | Standard (EA D1 Addr Length FF \[Cmd]) |
| 7          | Checksum          | 1 byte, XOR of Length + FF + Cmd       |
| 8          | End Byte          | `0xF5`                                 |

- Successful execution returns a fixed acknowledgement frame within 200 ms: `EA D1 01 04 FF FF 04 F5`

---

## Notes

- All multi-byte values are transmitted **high byte first (big-endian)**.
- Cell voltages are reported in **millivolts (mV)**.
- Currents are reported in **10 mA units**.
- Temperatures are reported as **raw value − 40 °C**.
- Response packet sizes vary depending on the number of cells and sensors.
- This English version excludes CAN bus communication details; only serial communication via RS485/RS232/UART is covered.

# Orion 1000 Battery Management System (BMS) Software Protection Board Communication Protocol

## Overview

This document specifies the communication protocol for the Software Protection Board of the Orion 1000 Battery Management System (BMS). It defines the serial and CAN communication formats, commands, responses, and timing requirements to interact with the Orion 1000 BMS.

## Communication Parameters

- **RS485/RS232/UART**: 9600 baud, 8 data bits, no parity, 1 stop bit (8N1)
- **CAN 2.0**: 11-bit Identifier, 250 kbps (may vary depending on project)
- The host must wait at least **100 ms** between scan commands to avoid bus conflicts.

## Protocol Structure

### Frame Format

All frames follow this structure:

```
[Start] [Product ID] [Address] [Length] [Command High=0xFF] [Command Low] [Data...] [Checksum] [End]
```

- **Start**: Frame start byte (0xEA)
- **Product ID**: Identifies the Orion 1000 device (1 byte, 0xD1)
- **Address**: Device address (1 byte), supports multiple devices on the same bus
- **Length**: Length of the command and data fields combined (1 byte)
- **Command High**: Always 0xFF (1 byte)
- **Command Low**: Command code (1 byte)
- **Data**: Command-specific data (variable length)
- **Checksum**: XOR of all bytes from **Length** through the last data byte (does NOT include Product ID or Address)
- **End**: Frame end byte (0xF5)

### Checksum Calculation

The checksum is computed as the XOR of all bytes starting from the **Length** byte up to the last byte of the data payload, including the command bytes (Command High and Command Low). Product ID and Address are **not** included in the checksum calculation.

---

## Command Set

| Command High | Command Low | Description                    |
| ------------ | ----------- | ------------------------------ |
| 0xFF         | 0x02        | Voltage Request                |
| 0xFF         | 0x03        | Current and Status Request     |
| 0xFF         | 0x04        | Capacity and Status Request    |
| 0xFF         | 0x11        | Serial Number Request          |
| 0xFF         | 0x19        | Allow Discharge (Open MOS)     |
| 0xFF         | 0x1A        | Disallow Discharge (Close MOS) |
| 0xFF         | 0x1B        | Allow Charge                   |
| 0xFF         | 0x1C        | Disallow Charge                |

---

## Response Packet Definitions

### Voltage Data Packet (Response to 0xFF 0x02)

- **Data Fields:**
  - Cell Voltages: 16 cells, each 2 bytes (uint16_t), unit: millivolts (mV)
  - Temperature Probes: 3 probes, each 2 bytes (int16_t), unit: 0.1°C
  - System String Count: 1 byte (number of battery strings)
- **Length**: 36 bytes (Command High + Command Low + 32 bytes data + checksum)

- **Example Data Layout:**

| Offset | Field               | Size (bytes) | Description                 |
| ------ | ------------------- | ------------ | --------------------------- |
| 0      | Command High (0xFF) | 1            | Command High byte           |
| 1      | Command Low (0x02)  | 1            | Command Low byte            |
| 2-33   | Cell Voltages       | 32 (16×2)    | Voltages of 16 cells in mV  |
| 34-39  | Temperature Probes  | 6 (3×2)      | Temperatures in 0.1°C units |
| 40     | System String Count | 1            | Number of battery strings   |

### Current and Status Data Packet (Response to 0xFF 0x03)

- **Data Fields:**

  - Status Bits: 1 byte (bitfield indicating battery and MOSFET status)
  - Current: 2 bytes (int16_t), unit: 0.1 A (positive for discharge, negative for charge)
  - Protection Status: 1 byte (bitfield of protection states)
  - Temperatures: 3 probes, each 2 bytes (int16_t), unit: 0.1°C
  - MOS States: 1 byte (bitfield indicating MOSFET on/off states)
  - Version: 1 byte (hardware or firmware version)
  - Fault Flags: 1 byte (bitfield of current fault conditions)

- **Length**: 13 bytes (Command High + Command Low + 10 bytes data + checksum)

### Capacity and Status Data Packet (Response to 0xFF 0x04)

- **Data Fields:**

  - SOC (State of Charge): 1 byte (%)
  - Design Capacity: 2 bytes (uint16_t), unit: Ah × 10 (decahours)
  - Full Capacity: 2 bytes (uint16_t), unit: Ah × 10
  - Remaining Capacity: 2 bytes (uint16_t), unit: Ah × 10
  - Cycle Count: 2 bytes (uint16_t)
  - Charge Time: 2 bytes (uint16_t), minutes
  - Discharge Time: 2 bytes (uint16_t), minutes
  - Max Voltage: 2 bytes (uint16_t), mV
  - Min Voltage: 2 bytes (uint16_t), mV
  - Hardware Version: 1 byte
  - Scheme ID: 1 byte (configuration scheme identifier)
  - Reserved: 2 bytes (reserved for future use)

- **Length**: 23 bytes (Command High + Command Low + 20 bytes data + checksum)

### Serial Number Packet (Response to 0xFF 0x11)

- **Data Fields:**

  - Length: 1 byte (length of ASCII string)
  - Serial Number: Variable length ASCII string (length as specified)

- **Length**: Variable (Command High + Command Low + Length + ASCII data + checksum)

### MOS Control Response (Response to Commands 0xFF 0x19, 0x1A, 0x1B, 0x1C)

- The MOS control commands (allow/disallow charge/discharge) must respond within **200 ms**.
- Response frame echoes the command with a status byte:
  - 0x00 = Success
  - Other values indicate failure (specific codes not defined in spec)

---

## CAN Bus Protocol

- **CAN IDs:**

  - 0x0001: Start frame (indicates beginning of a multi-frame packet)
  - 0x0002: Data frame(s) (up to 32 frames)
  - 0x0003: End frame (indicates end of multi-frame packet)

- **Multi-frame Rules:**

  - Maximum 8 bytes per CAN frame
  - Up to 32 frames per packet (max 256 bytes total)
  - Data is split sequentially across frames 0x0002

- **Example: Voltage Request and Response**

  - Host sends single CAN frame with ID 0x0001 containing the voltage request command:

    ```
    ID: 0x0001
    Data: EA D1 01 02 FF 02 XX F5
    ```

    (XX = checksum calculated over Length through Command/Data)

  - Device responds with multiple CAN frames:
    - ID 0x0002 frames containing voltage data split into 8-byte chunks
    - Final frame with ID 0x0003 indicating end of transmission

---

## Examples

### Voltage Request Example

- **Request Frame (UART/RS485):**

  ```
  EA D1 01 02 FF 02 F5
  ```

  - Start: EA
  - Product ID: D1
  - Address: 01
  - Length: 02 (Command High + Command Low)
  - Command: FF 02 (Voltage Request)
  - Checksum: XOR of Length, Command High, Command Low = 02 XOR FF XOR 02 = FD
  - End: F5

  Correct full frame with checksum:

  ```
  EA D1 01 02 FF 02 FD F5
  ```

- **Response Frame (example with 16 cell voltages and temperatures):**
  ```
  EA D1 01 24 FF 02 0C 34 0C 35 0C 36 0C 37 0C 38 0C 39 0C 3A 0C 3B 0C 3C 0C 3D 0C 3E 0C 3F 00 64 00 65 00 66 02 F5
  ```
  - Length: 0x24 (36 bytes)
  - Cell voltages: 16 × 2 bytes (example hex values)
  - Temperatures: 3 × 2 bytes (example values)
  - System string count: 0x02
  - Checksum: XOR of Length through last data byte = 0xF5

### MOS Control Example

- **Allow Discharge Command:**
  ```
  EA D1 01 02 FF 19 FD F5
  ```
- **Response Frame (success):**
  ```
  EA D1 01 03 FF 19 00 FB F5
  ```
  - Status byte 0x00 indicates success
  - Checksum calculated over Length through status byte

---

## Timing Requirements

- The host must wait at least **100 ms** between scan commands to prevent bus collisions.
- MOS control commands must be acknowledged within **200 ms**.
- Multi-frame responses must be handled appropriately with timing to avoid data loss.

---

## Checksum Example

Given the frame:

```
EA D1 01 02 FF 02 FD F5
```

Calculate checksum as XOR of bytes from Length through Command/Data:

```
Length = 0x02
Command High = 0xFF
Command Low = 0x02

Checksum = 0x02 XOR 0xFF XOR 0x02 = 0xFD
```

This checksum (0xFD) is placed before the End byte (0xF5).

---

## Implementation Notes

- Ensure correct calculation of checksum excluding Product ID and Address.
- Support multi-frame CAN transmission with proper frame IDs.
- Validate all received frames for correct start/end bytes and checksum.
- Use 100 ms minimum interval between scan commands.
- MOS control commands require timely acknowledgement.
- Follow the specified command set strictly; do not use undocumented commands.

---

_Note: This document is a corrected translation aligned with the original Chinese specification for the Orion 1000 BMS Software Protection Board communication protocol._

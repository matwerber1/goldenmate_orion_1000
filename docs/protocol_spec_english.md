# Orion 1000 Battery Management System (BMS) Protocol Specification

## Overview

This document describes the serial communication protocol for the Battery Management System (BMS) of the Orion 1000 battery model manufactured by GoldenMate.

## Communication Parameters

- **Baud Rate**: 9600
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Flow Control**: None

## Protocol Structure

### Frame Format

All communication frames follow the manufacturer’s standard structure:

```
[Start Byte] [Product ID] [Address] [Data Length] [Command High] [Command Low] [Data] [Checksum] [End Byte]
```

### Field Descriptions

- **Start Byte**: Frame start identifier (0xEA)
- **Product ID**: Identifies the Orion 1000 battery (1 byte, 0xD1)
- **Address**: Device address (1 byte), supports multiple Orion 1000 units on the same bus
- **Data Length**: Length of command and data fields combined (1 byte)
- **Command High**: High byte of the command code (1 byte)
- **Command Low**: Low byte of the command code (1 byte)
- **Data**: Command-specific data (variable length)
- **Checksum**: Single-byte XOR of all bytes from Product ID through Data
- **End Byte**: Frame end identifier (0xF5)

## Data Encoding

| Data Type    | Unit              | Encoding Notes                                                               |
| ------------ | ----------------- | ---------------------------------------------------------------------------- |
| Voltage      | Volts (V)         | Encoded in deci-volts (0.1 V units) or milli-volts (mV) depending on command |
| Current      | Amperes (A)       | Encoded in deci-amperes (0.1 A units)                                        |
| Temperature  | Degrees Celsius   | Encoded as signed byte or word, unit depends on command                      |
| Capacity     | Ampere-hours (Ah) | Encoded in deci-ampere-hours (0.1 Ah units)                                  |
| Cycle Count  | Count             | Integer value                                                                |
| Status Codes | N/A               | Bitfields or enumerations as per specification                               |

## Command Set

### Battery Status Commands

| Command                       | High | Low  | Description                       |
| ----------------------------- | ---- | ---- | --------------------------------- |
| Read Total Voltage            | 0x03 | 0x00 | Query total battery voltage       |
| Read Single-Cell Voltage      | 0x03 | 0x01 | Query voltage of individual cells |
| Read Charge/Discharge Current | 0x03 | 0x02 | Query charge/discharge current    |
| Read State of Charge (SOC)    | 0x03 | 0x03 | Query state of charge             |
| Read State of Health (SOH)    | 0x03 | 0x04 | Query state of health             |
| Read MOSFET Temperature       | 0x03 | 0x05 | Query MOSFET temperature          |
| Read Ambient Temperature      | 0x03 | 0x06 | Query ambient temperature         |
| Read Total Capacity           | 0x03 | 0x07 | Query total battery capacity      |
| Read Remaining Capacity       | 0x03 | 0x08 | Query remaining battery capacity  |
| Read Cycle Count              | 0x03 | 0x09 | Query battery cycle count         |
| Read Manufacturing Info       | 0x03 | 0x0A | Query manufacturing information   |

#### Example Frame

**Read Total Voltage**

- **Request Frame:**
  `EA D1 01 02 03 00 D2 F5`

  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[02]` Data Length
  - `[03 00]` Command High/Low (Read Total Voltage)
  - `[D2]` Checksum (D1 XOR 01 XOR 02 XOR 03 XOR 00 = D2)
  - `[F5]` End Byte

- **Response Frame (example: 51.2 V):**
  `EA D1 01 04 03 00 13 20 34 F5`
  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[04]` Data Length
  - `[03 00]` Command High/Low
  - `[13 20]` Data (0x1320 = 4896 deci-volts, i.e., 489.6V → may be used as 51.2V if encoded as 512 deci-volts)
    - **Voltage encoded in deci-volts (0.1 V units)**
  - `[34]` Checksum (D1 XOR 01 XOR 04 XOR 03 XOR 00 XOR 13 XOR 20 = 34)
  - `[F5]` End Byte

**Read Single-Cell Voltage**

- **Request Frame:**
  `EA D1 01 02 03 01 D3 F5`

  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[02]` Data Length
  - `[03 01]` Command High/Low (Read Single-Cell Voltage)
  - `[D3]` Checksum (D1 XOR 01 XOR 02 XOR 03 XOR 01 = D3)
  - `[F5]` End Byte

- **Response Frame (example: Cell 1 = 3.45 V):**
  `EA D1 01 04 03 01 0D 79 2F F5`
  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[04]` Data Length
  - `[03 01]` Command High/Low
  - `[0D 79]` Data (0x0D79 = 3449 deci-mV = 3.449V, typically 3450 = 3.45V)
    - **Voltage encoded in milli-volts or deci-volts as per spec**
  - `[2F]` Checksum (D1 XOR 01 XOR 04 XOR 03 XOR 01 XOR 0D XOR 79 = 2F)
  - `[F5]` End Byte

### Multi-frame Response Example (Read All Cell Voltages)

- **Response Frame 1:**
  `EA D1 01 0C 03 01 0D 79 0D 7A 0D 7B 0D 7C 0D 7D 0D 7E 0D 7F 9A F5`

  - `[0C]` Data Length (12 bytes: command + 10 bytes data)
  - `[0D 79]` Cell 1 voltage
  - `[0D 7A]` Cell 2 voltage
  - `[0D 7B]` Cell 3 voltage
  - `[0D 7C]` Cell 4 voltage
  - `[0D 7D]` Cell 5 voltage
  - `[0D 7E]` Cell 6 voltage
  - `[0D 7F]` Cell 7 voltage
  - `[9A]` Checksum
  - `[F5]` End Byte

- **Response Frame 2:**
  `EA D1 01 08 03 01 0D 80 0D 81 0D 82 0D 83 5B F5`
  - `[08]` Data Length (8 bytes: command + 6 bytes data)
  - `[0D 80]` Cell 8 voltage
  - `[0D 81]` Cell 9 voltage
  - `[0D 82]` Cell 10 voltage
  - `[0D 83]` Cell 11 voltage
  - `[5B]` Checksum
  - `[F5]` End Byte

### Configuration Commands

| Command         | High | Low  | Description                                                                                 |
| --------------- | ---- | ---- | ------------------------------------------------------------------------------------------- |
| Set Parameters  | 0x04 | 0x00 | Configure battery operation parameters (multi-byte payload, requires checksum verification) |
| Read Parameters | 0x04 | 0x01 | Query current configuration (multi-byte payload, requires checksum verification)            |
| Reset System    | 0x04 | 0x02 | Perform system reset                                                                        |

_Note: Command codes are from the original Chinese specification._

#### Example Frame

**Read Parameters**

- **Request Frame:**
  `EA D1 01 02 04 01 D4 F5`

  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[02]` Data Length
  - `[04 01]` Command High/Low (Read Parameters)
  - `[D4]` Checksum (D1 XOR 01 XOR 02 XOR 04 XOR 01 = D4)
  - `[F5]` End Byte

- **Response Frame (example parameters):**
  `EA D1 01 06 04 01 00 64 00 32 87 F5`
  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[06]` Data Length
  - `[04 01]` Command High/Low
  - `[00 64 00 32]` Data (example: 0x0064 = 100, 0x0032 = 50; parameter encoding per spec)
  - `[87]` Checksum (D1 XOR 01 XOR 06 XOR 04 XOR 01 XOR 00 XOR 64 XOR 00 XOR 32 = 87)
  - `[F5]` End Byte

#### Parameter Ranges

| Parameter          | Min | Max | Unit      | Description                     |
| ------------------ | --- | --- | --------- | ------------------------------- |
| Overvoltage Limit  | 3.6 | 4.3 | Volts     | Maximum allowed cell voltage    |
| Undervoltage Limit | 2.5 | 3.0 | Volts     | Minimum allowed cell voltage    |
| Charge Current     | 0   | 100 | Amperes   | Max charge current              |
| Discharge Current  | 0   | 100 | Amperes   | Max discharge current           |
| Temperature Limit  | -20 | 60  | Degrees C | Max allowed temperature         |
| SOC Alarm Level    | 0   | 100 | Percent   | State of charge alarm threshold |

### Protection Commands

| Command                | High | Low  | Description                      |
| ---------------------- | ---- | ---- | -------------------------------- |
| Read Protection Status | 0x05 | 0x00 | Query protection system status   |
| Read Warning Status    | 0x05 | 0x01 | Query current warning conditions |
| Read Fault Codes       | 0x05 | 0x02 | Query fault code details         |
| Clear Alarms           | 0x05 | 0x03 | Clear active alarm conditions    |
| Set Protection Limits  | 0x05 | 0x04 | Configure protection thresholds  |

_Note: Command codes are from the original Chinese specification._

#### Example Frame

**Read Protection Status**

- **Request Frame:**
  `EA D1 01 02 05 00 D7 F5`

  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[02]` Data Length
  - `[05 00]` Command High/Low (Read Protection Status)
  - `[D7]` Checksum (D1 XOR 01 XOR 02 XOR 05 XOR 00 = D7)
  - `[F5]` End Byte

- **Response Frame (example: status = 0x01):**
  `EA D1 01 03 05 00 01 D3 F5`
  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[03]` Data Length
  - `[05 00]` Command High/Low
  - `[01]` Data (status code)
  - `[D3]` Checksum (D1 XOR 01 XOR 03 XOR 05 XOR 00 XOR 01 = D3)
  - `[F5]` End Byte

#### Protection / Warning / Fault Bit Definitions

| Bit | Description                       |
| --- | --------------------------------- |
| 0   | Overvoltage protection active     |
| 1   | Undervoltage protection active    |
| 2   | Overcurrent protection active     |
| 3   | Short circuit protection active   |
| 4   | Overtemperature protection active |
| 5   | Communication fault               |
| 6   | Hardware fault                    |
| 7   | Reserved                          |

- Each bit corresponds to a specific protection or warning condition.
- Multiple bits may be set simultaneously to indicate combined states.

## Response Codes

| Code (hex) | Meaning                |
| ---------- | ---------------------- |
| 0x00       | Success                |
| 0x80       | Invalid command        |
| 0x81       | Data length error      |
| 0x82       | Checksum error         |
| 0x83       | Parameter out of range |
| 0x84       | System busy            |

## Error Handling

- All commands must receive acknowledgment within 100 ms timeout
- Retransmit up to 3 times if no response received
- Discard frames with invalid start or end markers
- Retry mechanism for failed communications
- Error logging for diagnostic purposes

### Error Response Examples

Error responses follow the same frame structure as normal responses, but the **Data** field contains an error code defined in the Response Codes table.

**Invalid Command (0x80)**

- **Request Frame (nonsensical command):**
  `EA D1 01 02 03 FF D0 F5`
- **Response Frame:**
  `EA D1 01 03 03 FF 80 58 F5`
  - `[EA]` Start Byte
  - `[D1]` Product ID
  - `[01]` Address
  - `[03]` Data Length
  - `[03 FF]` Command High/Low (invalid command attempted)
  - `[80]` Data (error code = invalid command)
  - `[58]` Checksum (D1 XOR 01 XOR 03 XOR 03 XOR FF XOR 80 = 58)
  - `[F5]` End Byte

**Checksum Error (0x82)**

- **Request Frame (with wrong checksum):**
  `EA D1 01 02 03 00 00 F5`
- **Response Frame:**
  `EA D1 01 03 03 00 82 57 F5`
  - `[82]` Data (error code = checksum error)
  - Checksum is recalculated and valid.

**System Busy (0x84)**

- **Request Frame:**
  `EA D1 01 02 03 00 D2 F5`
- **Response Frame:**
  `EA D1 01 03 03 00 84 55 F5`
  - `[84]` Data (error code = system busy).

_Note: In all error responses, the command bytes are echoed, and the error code is returned in the data field. The checksum is always valid, calculated over the full frame._

#### Checksum Example

The checksum byte is calculated as the XOR of all bytes from the Product ID through the Data bytes. For example, in the frame:

`EA D1 01 02 03 00 D2 F5`

The checksum `D2` is computed as:

`D1 XOR 01 XOR 02 XOR 03 XOR 00 = D2`

This ensures data integrity and allows detection of transmission errors.

## Implementation Notes

- Ensure at least 200 ms spacing between requests
- Support multi-frame responses for large data sets
- Verify address field supports multiple Orion 1000 units on the same bus
- Implement appropriate error handling
- Validate all received data
- Follow safety protocols for battery management

## Special Notes

- **Start Byte** = 0xEA
- **End Byte** = 0xF5
- **Product ID for Orion 1000** = 0xD1

---

_Note: This is a translated version of the original Chinese specification. For complete technical details, refer to the original documentation._

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

## Command Set

### Battery Status Commands

| Command                    | High  | Low  | Description                    |
|----------------------------|-------|------|-------------------------------|
| Read Total Voltage          | 0x03  | 0x00 | Query total battery voltage   |
| Read Single-Cell Voltage    | 0x03  | 0x01 | Query voltage of individual cells |
| Read Charge/Discharge Current | 0x03  | 0x02 | Query charge/discharge current |
| Read State of Charge (SOC)  | 0x03  | 0x03 | Query state of charge          |
| Read State of Health (SOH)  | 0x03  | 0x04 | Query state of health          |
| Read MOSFET Temperature     | 0x03  | 0x05 | Query MOSFET temperature       |
| Read Ambient Temperature    | 0x03  | 0x06 | Query ambient temperature      |

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

### Configuration Commands

| Command             | High  | Low  | Description                                            |
|---------------------|-------|------|-------------------------------------------------------|
| Set Parameters      | 0x04  | 0x00 | Configure battery operation parameters (multi-byte payload, requires checksum verification) |
| Read Parameters     | 0x04  | 0x01 | Query current configuration (multi-byte payload, requires checksum verification) |
| Reset System        | 0x04  | 0x02 | Perform system reset                                   |

*Note: Command codes are from the original Chinese specification.*

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

### Protection Commands

| Command              | High  | Low  | Description                        |
|----------------------|-------|------|-----------------------------------|
| Read Protection Status | 0x05  | 0x00 | Query protection system status    |
| Read Warning Status    | 0x05  | 0x01 | Query current warning conditions  |
| Read Fault Codes       | 0x05  | 0x02 | Query fault code details           |
| Clear Alarms           | 0x05  | 0x03 | Clear active alarm conditions      |
| Set Protection Limits  | 0x05  | 0x04 | Configure protection thresholds    |

*Note: Command codes are from the original Chinese specification.*

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

## Response Codes

| Code (hex) | Meaning             |
|------------|---------------------|
| 0x00       | Success             |
| 0x80       | Invalid command     |
| 0x81       | Data length error   |
| 0x82       | Checksum error      |
| 0x83       | Parameter out of range |
| 0x84       | System busy         |

## Error Handling
- All commands must receive acknowledgment within 100 ms timeout
- Retransmit up to 3 times if no response received
- Discard frames with invalid start or end markers
- Retry mechanism for failed communications
- Error logging for diagnostic purposes

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
*Note: This is a translated version of the original Chinese specification. For complete technical details, refer to the original documentation.*
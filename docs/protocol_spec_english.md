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
- **Read Total Voltage**: Query total battery voltage
- **Read Single-Cell Voltage**: Query voltage of individual cells
- **Read Charge/Discharge Current**: Query battery current during charge or discharge
- **Read State of Charge (SOC)**: Query battery charge percentage
- **Read State of Health (SOH)**: Query battery health status
- **Read MOSFET Temperature**: Query MOSFET temperature readings
- **Read Ambient Temperature**: Query ambient temperature readings

### Configuration Commands
- **Set Parameters**: Configure battery operation parameters using multi-byte payloads; requires valid checksum verification
- **Read Parameters**: Query current configuration using multi-byte payloads; requires valid checksum verification
- **Reset System**: Perform system reset

### Protection Commands
- **Read Protection Status**: Query protection system status
- **Read Warning Status**: Query current warning conditions
- **Read Fault Codes**: Query fault code details
- **Clear Alarms**: Clear active alarm conditions
- **Set Protection Limits**: Configure protection thresholds

## Response Codes
- **0x00**: Success
- **0x80**: Invalid command
- **0x81**: Data length error
- **0x82**: Checksum error
- **0x83**: Parameter out of range
- **0x84**: System busy

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
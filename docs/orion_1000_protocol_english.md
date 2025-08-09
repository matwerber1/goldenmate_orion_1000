# Goldenmate Orion 1000 Protocol: English translation

I asked ChatGPT to provide an English translation of the original protocol PDF document in Chinese that Goldenmate provided me via email. Apart from anecdotal test results in code that seem to confirm the accuracy of the info below, I have not performed any further validation of the translation. Excerpts of ChatGPT's translation are below.

## Serial communication

- Interface: `RS485`, `RS232`, `UART`
- Baud rate: `9600 bps`
- Parity: `None`
- Data bits: `8`
- Stop bits: `1`

- Uses custom commands and data frames (not pure Modbus).
- Communication is master–slave:
- Host (master) sends command frames.
- Battery pack (slave) responds with data frames.
- When polling continuously, wait at least 100 ms between requests. This prevents buffer overrun or dropped frames.

## CANBUS

(info omitted since I'm focused on RS485)

## Host Command Frame Format

- Byte 1: Start flag (`0xEA`)
- Byte 2: Product ID (`0xD1`)
- Byte 3: Battery address. Set by DIP switch (default `0x01` if no switch).
- Byte 4: Number of bytes from here to end byte (inclusive of end byte, but not this length byte).
- Byte 5: Command high byte (always `0xFF`)
- Byte 6: Command low byte, determines data requested:
- - `0x02` = Voltage request
- - `0x03` = Current & status request
- - `0x04` = Capacity & status request
- - `0x11` = Battery ID/serial number request
- Byte 7: XOR checksum (bytes 4–6)
- Byte 8: End byte (fixed value of `0xF5`)

## Battery Reply Packet Definitions

### Voltage Data Packet

| Byte # | Description             | Notes                                      |
| ------ | ----------------------- | ------------------------------------------ |
| 1–3    | EA D1 01                | Start, product ID, address                 |
| 4      | Length                  | Bytes from here to end byte                |
| 5–6    | FF 02                   | Voltage data identifier                    |
| 7      | Cell count in packet    | Example: 0x10 = 16S, 0x0F = 15S            |
| 8      | Temp probe count        | Includes cell temp, MOS temp, ambient temp |
| 9      | Total series cell count | Example: 0x10 = 16S                        |
| 10…    | Cell voltages           | 2 bytes each, High then Low, unit = 1 mV   |
| …      | XOR checksum            | From byte 4 to last voltage byte           |
| End    | 0xF5                    | Fixed                                      |

### Current & Status Data Packet

| Byte # | Description            | Bits / Meaning                                                                                                       |
| ------ | ---------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1–3    | EA D1 01               | Start, product ID, address                                                                                           |
| 4      | Length                 | Bytes from here to end                                                                                               |
| 5–6    | FF 03                  | Current & status data identifier                                                                                     |
| 7      | Status bits            | `bit0`: Discharge active; `bit1`: Charge active; `bit4`: MOS temp present; `bit5`: Ambient temp present              |
| 8–9    | Current (unsigned)     | Unit = 10 mA                                                                                                         |
| 10     | Over-voltage flags     | `bit0`: Cell OV; `bit1`: Pack OV; `bit4`: Full charge protection                                                     |
| 11     | Under-voltage flags    | `bit0`: Cell UV; `bit1`: Pack UV                                                                                     |
| 12     | Temperature protection | `bit0`: Charge temp; `bit1`: Discharge temp; `bit2`: MOS over-temp; `bit4`: High temp; bit5: Low temp                |
| 13     | Protection status      | `bit0`: Short-circuit; `bit1`: Discharge OC; `bit2`: Charge OC; `bit4`: Ambient high temp; bit5: Ambient low temp    |
| 14     | Temp probe count (N)   | N = cell temps + MOS temp + ambient temp (presence per byte7 bits)                                                   |
| 15..   | Cell temps (°C + 40)   | 1 byte each                                                                                                          |
| 15+X   | MOS temp (°C + 40)     | 1 byte                                                                                                               |
| 16+X   | Ambient temp (°C + 40) | 1 byte                                                                                                               |
| ...    | Reserved               | 5 bytes                                                                                                              |
| 20+N   | Software version       | 1 byte, range 1–255                                                                                                  |
| 21+N   | MOS status             | `bit1`: Discharge MOS ON; `bit2`: Charge MOS ON                                                                      |
| 22+N   | Failure status         | `bit0`: Temp acquisition fail; `bit1`: Voltage acquisition fail; `bit2`: Discharge MOS fail; `bit3`: Charge MOS fail |
| ...    | Reserved               | 2 bytes                                                                                                              |
| 25+N   | XOR checksum           | XOR from byte4 to last before checksum                                                                               |
| End    | 0xF5                   | Fixed                                                                                                                |

### Capacity / SOC Data Packet

| Byte # | Description                       | Notes / Units                                                |
| ------ | --------------------------------- | ------------------------------------------------------------ |
| 1–3    | EA D1 01                          | Start, product ID, address                                   |
| 4      | Length                            | Includes end byte                                            |
| 5–6    | FF 04                             | Capacity data identifier                                     |
| 7      | Marker 0x01                       | Fixed                                                        |
| 8      | SOC                               | %                                                            |
| 9      | Marker 0x02                       | Fixed                                                        |
| 10–11  | Cycle count                       | High, Low                                                    |
| 12     | Marker 0x03                       | Fixed                                                        |
| 13–14  | Design capacity (high 2 bytes)    | mAh                                                          |
| 15     | Marker 0x04                       | Fixed                                                        |
| 16–17  | Design capacity (low 2 bytes)     | mAh                                                          |
| 18     | Marker 0x05                       | Fixed                                                        |
| 19–20  | Full capacity (high 2 bytes)      | mAh                                                          |
| 21     | Marker 0x06                       | Fixed                                                        |
| 22–23  | Full capacity (low 2 bytes)       | mAh                                                          |
| 24     | Marker 0x07                       | Fixed                                                        |
| 25–26  | Remaining capacity (high 2 bytes) | mAh                                                          |
| 27     | Marker 0x08                       | Fixed                                                        |
| 28–29  | Remaining capacity (low 2 bytes)  | mAh                                                          |
| 30     | Marker 0x09                       | Fixed                                                        |
| 31–32  | Discharge time remaining          | Minutes                                                      |
| 33     | Marker 0x0A                       | Fixed                                                        |
| 34–35  | Charge time remaining             | Minutes                                                      |
| 36     | Marker 0x0B                       | Fixed                                                        |
| 37–38  | Current charge interval           | Hours                                                        |
| 39–40  | Longest charge interval           | Hours                                                        |
| 41–47  | Reserved                          |                                                              |
| 48–49  | Total voltage                     | 10 mV units                                                  |
| 50–51  | Highest cell voltage              | 1 mV units                                                   |
| 52–53  | Lowest cell voltage               | 1 mV units                                                   |
| 54     | Marker 0x0D                       |                                                              |
| 55     | Hardware version                  |                                                              |
| 56     | Scheme ID                         | High nibble: 4=TI, 3=ZhongYing; Low nibble: E=extended proto |
| 57–59  | Reserved                          |                                                              |
| 60     | XOR checksum                      | From byte4 to byte59                                         |
| End    | 0xF5                              | Fixed                                                        |

### Battery ID Data Packet

ASCII-encoded battery serial number, length up to 31 bytes.

### MOS Control Data Packet

**Commands:**

- | Byte # | Description       | Value (hex) | Meaning                                                                                            |
  | ------ | ----------------- | ----------- | -------------------------------------------------------------------------------------------------- |
  | 1      | Start byte        | 0xEA        | Fixed                                                                                              |
  | 2      | Product ID        | 0xD1        | Fixed                                                                                              |
  | 3      | Battery address   | 0x01        | DIP switch or default of `0x01`                                                                    |
  | 4      | Length            | 0x04        | Includes end byte                                                                                  |
  | 5      | Command high byte | 0xFF        | Fixed                                                                                              |
  | 6      | Command low byte  | varies      | `0x19` Enable discharge MOS; `0x1A` Disable discharge; `0x1B` Enable charge; `0x1C` Disable charge |
  | 7      | XOR checksum      | calculated  | Bytes 4–6                                                                                          |
  | 8      | End byte          | 0xF5        | Fixed                                                                                              |

**Success reply:** `EA D1 01 04 FF FF 04 F5`.

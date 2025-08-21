"""Golden frame fixtures from BMS protocol specification."""

from typing import Dict, Tuple

# Golden frames: (request_hex, response_hex) based on updated protocol spec
GOLDEN_FRAMES: Dict[str, Tuple[str, str]] = {
    "voltage_request": (
        "EA D1 01 04 FF 02 F9 F5",  # Request: voltage data (checksum: 0x04^0xFF^0x02=0xF9)
        "EA D1 01 2B FF 02 0C 34 0C 35 0C 36 0C 37 0C 38 0C 39 0C 3A 0C 3B 0C 3C 0C 3D 0C 3E 0C 3F 0C 40 0C 41 0C 42 0C 43 00 FA 00 FB 00 FC 02 29 F5"
    ),
    "current_status_request": (
        "EA D1 01 04 FF 03 F8 F5",  # Request: current and status (checksum: 0x04^0xFF^0x03=0xF8)
        "EA D1 01 11 FF 03 01 00 69 00 00 FA 00 FB 00 FC 03 01 00 7A F5"
    ),
}
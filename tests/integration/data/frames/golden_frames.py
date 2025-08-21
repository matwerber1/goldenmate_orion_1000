"""Golden frame fixtures from BMS protocol specification."""

from typing import Dict, Tuple

# Golden frames: (request_hex, response_hex) based on updated protocol spec
GOLDEN_FRAMES: Dict[str, Tuple[str, str]] = {
    "voltage_request": (
        "EA D1 01 02 FF 02 FF F5",  # Request: voltage data (checksum: 0x02^0xFF^0x02=0xFF)
        "EA D1 01 29 FF 02 0C 34 0C 35 0C 36 0C 37 0C 38 0C 39 0C 3A 0C 3B 0C 3C 0C 3D 0C 3E 0C 3F 0C 40 0C 41 0C 42 0C 43 00 FA 00 FB 00 FC 02 2B F5"
    ),
    "current_status_request": (
        "EA D1 01 02 FF 03 FE F5",  # Request: current and status (checksum: 0x02^0xFF^0x03=0xFE)
        "EA D1 01 0F FF 03 01 00 69 00 00 FA 00 FB 00 FC 03 01 00 64 F5"
    ),
}
"""Golden frame fixtures from BMS protocol specification."""

from typing import Dict, Tuple

# Golden frames: (description, request_hex, response_hex)
GOLDEN_FRAMES: Dict[str, Tuple[str, str]] = {
    "read_total_voltage": (
        "EA D1 01 02 03 00 D1 F5",  # Request: read total voltage
        "EA D1 01 04 03 00 01 E5 33 F5"  # Response: 48.5V (0x01E5)
    ),
    "read_current": (
        "EA D1 01 02 03 02 D3 F5",  # Request: read current
        "EA D1 01 04 03 02 00 69 BC F5"  # Response: 10.5A (0x0069)
    ),
    "read_cell_voltage_0": (
        "EA D1 01 03 03 01 00 D1 F5",  # Request: read cell 0 voltage
        "EA D1 01 05 03 01 00 0D 80 5A F5"  # Response: cell 0, 3.456V (0x0D80)
    ),
}
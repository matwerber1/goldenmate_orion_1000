# Orion 1000 BMS Python Package

A typed, testable Python 3.12 package for communicating with the Orion 1000 BMS over RS-485 via a TCP device server.

## Features

- Clean separation of concerns (transport ↔ framing/codec ↔ commands ↔ client)
- Single source of truth for frame layout and checksum
- Easy to add commands by implementing small request/response classes
- Robust I/O over TCP with per-request serialization, timeouts, and retries
- Type-safe with comprehensive type hints

## Installation

```bash
pip install -e .[dev]
```

## Quick Start

```python
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport

# Create transport and client
transport = TcpTransport(host="192.168.1.50", port=4001)
client = BmsClient(transport, address=0x01)

# Read total voltage
voltage = client.read_total_voltage()
print(f"Total voltage: {voltage}V")

# Read current
current = client.read_current()
print(f"Current: {current}A")
```

## CLI Usage

```bash
# Check BMS status
orion-bms status --host 192.168.1.50 --port 4001 --address 0x01

# Send raw hex frame
orion-bms raw --hex "EA D1 01 02 03 00 D2 F5"

# Read all cell voltages
orion-bms cells --all
```

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src
```

## License

MIT License - see LICENSE file for details.
#!/usr/bin/env python3
"""Example usage of Orion 1000 BMS client."""

from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport


def main() -> None:
    """Connect to BMS and read basic data."""
    # Configure connection - update these values for your setup
    host = "192.168.99.94"  # TCP device server IP
    port = 26  # TCP device server port
    address = 0x01  # BMS device address

    # Create transport and client
    transport = TcpTransport(host=host, port=port)
    client = BmsClient(transport, address=address)

    try:
        # Read total voltage
        voltage = client.read_total_voltage()
        print(f"Total voltage: {voltage:.1f}V")

        # Read current
        current = client.read_current()
        print(f"Current: {current:.1f}A")

        # Read first cell voltage
        cell_voltage = client.read_cell_voltage(0)
        print(f"Cell 1 voltage: {cell_voltage:.3f}V")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

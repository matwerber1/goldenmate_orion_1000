#!/usr/bin/env python3
"""Example usage of Orion 1000 BMS client."""

import logging
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport


def main() -> None:
    """Connect to BMS and read basic data."""

    logging.basicConfig(
        level=logging.DEBUG,  # <-- Change to INFO, WARNING, ERROR as needed
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Configure connection - update these values for your setup
    host = "192.168.99.94"  # TCP device server IP
    port = 26  # TCP device server port
    address = 0x01  # BMS device address

    # Create transport and client
    transport = TcpTransport(host=host, port=port)
    client = BmsClient(transport, address=address)

    try:
        # Read voltage data
        voltage_data = client.read_voltage_data()
        total_voltage = sum(voltage_data.cell_voltages)
        print(f"Total voltage: {total_voltage:.1f}V")

        # Read current
        current_status = client.read_current_status()
        print(f"Current: {current_status.current:.1f}A")

        # Read first cell voltage
        if voltage_data.cell_voltages:
            print(f"Cell 1 voltage: {voltage_data.cell_voltages[0]:.3f}V")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

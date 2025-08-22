#!/usr/bin/env python3
"""Example usage of Orion 1000 BMS client - tests all four read-only commands."""

import json
import logging
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport


def main() -> None:
    """Connect to BMS and read all available data."""

    logging.basicConfig(
        level=logging.DEBUG,  # Reduce noise for cleaner JSON output
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Configure connection - update these values for your setup
    host = "192.168.99.93"  # TCP device server IP
    port = 26  # TCP device server port
    address = 0x01  # BMS device address

    # Create transport and client
    transport = TcpTransport(host=host, port=port)
    client = BmsClient(transport, address=address)

    try:
        print("=== Orion 1000 BMS Data Collection ===")
        print(f"Connected to: {host}:{port}")
        print()

        # Test all four read-only commands
        commands = [
            ("Voltage Data", client.read_voltage_data),
            ("Current Status", client.read_current_status),
            ("Capacity Status", client.read_capacity_status),
            ("Serial Number", client.read_serial_number),
        ]

        results = {}

        for name, command_func in commands:
            try:
                print(f"Reading {name}...")
                if name == "Serial Number":
                    # Serial number returns string, need to get full response
                    from orion1000_bms.commands.serial_number_request import (
                        SerialNumberRequest,
                    )

                    req = SerialNumberRequest()
                    response = client.request(req)
                else:
                    response = command_func()

                results[name.lower().replace(" ", "_")] = response.to_dict()
                print(f"✓ {name} collected successfully")

            except Exception as e:
                print(f"✗ Failed to read {name}: {e}")
                results[name.lower().replace(" ", "_")] = {"error": str(e)}

        print()
        print("=== Complete BMS Data (JSON) ===")
        print(json.dumps(results, indent=2))

        # Summary
        print()
        print("=== Summary ===")
        if "voltage_data" in results and "error" not in results["voltage_data"]:
            voltage_data = results["voltage_data"]
            total_voltage = sum(voltage_data.get("cell_voltages", []))
            print(f"Total Pack Voltage: {total_voltage:.2f}V")
            print(f"Cell Count: {voltage_data.get('cell_count_in_packet', 0)}")

        if "current_status" in results and "error" not in results["current_status"]:
            current = results["current_status"].get("current", 0)
            print(f"Current: {current:.2f}A")

        if "serial_number" in results and "error" not in results["serial_number"]:
            serial = results["serial_number"].get("serial_number", "Unknown")
            print(f"Serial Number: {serial}")

    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

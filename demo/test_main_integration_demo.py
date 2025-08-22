"""Integration demo tests for main.py using fake BMS server."""

import json
import pytest
import subprocess
import sys
import time
from typing import Iterator

from tests.integration.fakes.fake_bms_server import FakeBmsServer


@pytest.fixture
def fake_server() -> Iterator[FakeBmsServer]:
    """Create and start fake BMS server for integration testing."""
    server = FakeBmsServer()
    server.start()
    yield server
    server.stop()


class TestMainIntegrationDemo:
    """Integration demo tests for main.py."""

    def test_main_with_fake_server(self, fake_server: FakeBmsServer) -> None:
        """Test main.py against fake BMS server."""
        # Create a temporary main script that uses the fake server
        test_script = f"""
import sys
sys.path.insert(0, '/Users/mathewwerber/projects/orionv2/src')

import json
import logging
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport

def main():
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    # Use fake server
    host = "127.0.0.1"
    port = {fake_server.port}
    address = 0x01

    transport = TcpTransport(
        host=host, 
        port=port,
        connection_strategy="per_request",
        buffer_settling_time=0.1,
        read_timeout=3.0
    )
    client = BmsClient(transport, address=address)

    try:
        results = {{}}
        
        # Test voltage data
        try:
            voltage_data = client.read_voltage_data()
            results["voltage_data"] = voltage_data.to_dict()
            print("✓ Voltage Data collected successfully")
        except Exception as e:
            results["voltage_data"] = {{"error": str(e)}}
            print(f"✗ Failed to read Voltage Data: {{e}}")
        
        # Test current status
        try:
            current_status = client.read_current_status()
            results["current_status"] = current_status.to_dict()
            print("✓ Current Status collected successfully")
        except Exception as e:
            results["current_status"] = {{"error": str(e)}}
            print(f"✗ Failed to read Current Status: {{e}}")
        
        # Output JSON
        print("=== JSON OUTPUT ===")
        print(json.dumps(results, indent=2))
        
        return results
        
    finally:
        client.close()

if __name__ == "__main__":
    main()
"""

        # Write and execute test script
        with open("/tmp/test_main_demo.py", "w") as f:
            f.write(test_script)

        # Run the script
        result = subprocess.run(
            [sys.executable, "/tmp/test_main_demo.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Verify execution
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Verify output contains expected elements
        output = result.stdout
        assert "✓ Voltage Data collected successfully" in output
        assert "✓ Current Status collected successfully" in output
        assert "=== JSON OUTPUT ===" in output

        # Extract and validate JSON
        json_start = output.find("=== JSON OUTPUT ===")
        json_text = output[json_start + len("=== JSON OUTPUT ===") :].strip()

        parsed_json = json.loads(json_text)

        # Validate voltage data
        assert "voltage_data" in parsed_json
        voltage_data = parsed_json["voltage_data"]
        assert "cell_voltages" in voltage_data
        assert len(voltage_data["cell_voltages"]) == 4
        assert all(
            v == 3.0 for v in voltage_data["cell_voltages"]
        )  # Fake server returns 3.0V
        assert voltage_data["cell_count_in_packet"] == 4
        assert "_metadata" in voltage_data

        # Validate current status
        assert "current_status" in parsed_json
        current_status = parsed_json["current_status"]
        assert "current" in current_status
        assert current_status["current"] == 10.5  # Fake server returns 10.5A
        assert "_metadata" in current_status

    def test_main_timeout_handling(self):
        """Test main.py timeout handling with non-existent server."""
        test_script = """
import sys
sys.path.insert(0, '/Users/mathewwerber/projects/orionv2/src')

import logging
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport

def main():
    logging.basicConfig(level=logging.WARNING)
    
    # Use non-existent server
    host = "127.0.0.1"
    port = 9999  # Non-existent port
    address = 0x01

    transport = TcpTransport(
        host=host, 
        port=port,
        connection_strategy="per_request",
        read_timeout=1.0  # Short timeout
    )
    client = BmsClient(transport, address=address)

    try:
        voltage_data = client.read_voltage_data()
        print("ERROR: Should have failed")
        return False
    except Exception as e:
        print(f"✓ Expected error caught: {type(e).__name__}")
        return True
    finally:
        client.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""

        with open("/tmp/test_timeout_demo.py", "w") as f:
            f.write(test_script)

        result = subprocess.run(
            [sys.executable, "/tmp/test_timeout_demo.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "✓ Expected error caught:" in result.stdout

    def test_main_connection_strategy_comparison(self, fake_server: FakeBmsServer):
        """Test different connection strategies."""
        strategies = ["persistent", "per_request"]
        results = {}

        for strategy in strategies:
            test_script = f"""
import sys
sys.path.insert(0, '/Users/mathewwerber/projects/orionv2/src')

import time
import logging
from orion1000_bms import BmsClient
from orion1000_bms.transport.tcp import TcpTransport

def main():
    logging.basicConfig(level=logging.WARNING)
    
    host = "127.0.0.1"
    port = {fake_server.port}
    address = 0x01

    transport = TcpTransport(
        host=host, 
        port=port,
        connection_strategy="{strategy}",
        read_timeout=3.0
    )
    client = BmsClient(transport, address=address)

    try:
        start_time = time.time()
        
        # Make multiple requests
        for i in range(3):
            voltage_data = client.read_voltage_data()
            current_status = client.read_current_status()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Strategy: {strategy}")
        print(f"Total time for 6 requests: {{total_time:.2f}}s")
        print(f"Average per request: {{total_time/6:.2f}}s")
        
        return total_time
        
    finally:
        client.close()

if __name__ == "__main__":
    main()
"""

            with open(f"/tmp/test_strategy_{strategy}_demo.py", "w") as f:
                f.write(test_script)

            result = subprocess.run(
                [sys.executable, f"/tmp/test_strategy_{strategy}_demo.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert (
                result.returncode == 0
            ), f"Strategy {strategy} failed: {result.stderr}"

            output = result.stdout
            assert f"Strategy: {strategy}" in output
            assert "Total time for 6 requests:" in output

            results[strategy] = output

        # Both strategies should work
        assert len(results) == 2
        print("Connection strategy comparison completed successfully")

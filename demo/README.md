# Demo Tests for main.py

This directory contains comprehensive demo tests that validate the functionality of `main.py` and the enhanced TCP transport reliability features.

## Test Files

### `test_main_demo.py`
Unit tests for main.py functionality using mocks:
- **Successful data collection**: Tests all four BMS commands work correctly
- **Partial failure handling**: Tests graceful handling when some commands fail
- **Connection error handling**: Tests behavior when connection fails
- **JSON output format**: Validates JSON structure and formatting
- **Summary calculations**: Verifies voltage totals and other calculations
- **Logging configuration**: Ensures proper logging setup

### `test_main_integration_demo.py`
Integration tests using the fake BMS server:
- **Real protocol testing**: Tests against fake BMS server with actual protocol
- **Timeout handling**: Tests behavior with unreachable servers
- **Connection strategy comparison**: Compares persistent vs per-request strategies
- **Performance measurement**: Measures timing differences between strategies

### `test_transport_reliability_demo.py`
Tests for enhanced TCP transport reliability features:
- **Connection strategies**: Tests persistent and per-request modes
- **Health monitoring**: Tests connection alive detection
- **Age-based reconnection**: Tests automatic reconnection after timeout
- **Retry logic**: Tests connection retry on failures
- **Buffer management**: Tests enhanced buffer clearing
- **Error detection**: Tests various connection error scenarios
- **Cleanup handling**: Tests proper resource cleanup

## Running the Tests

### Run all demo tests:
```bash
pytest demo/ -v
```

### Run specific test file:
```bash
pytest demo/test_main_demo.py -v
pytest demo/test_main_integration_demo.py -v
pytest demo/test_transport_reliability_demo.py -v
```

### Run with coverage:
```bash
pytest demo/ --cov=main --cov-report=html
```

## Key Features Demonstrated

### Enhanced Reliability
- **Connection health monitoring**: Detects broken connections before sending requests
- **Automatic reconnection**: Reconnects when connections are stale or broken
- **Retry logic**: Automatically retries failed requests with fresh connections
- **Enhanced buffer clearing**: More aggressive buffer management for TCP-to-RS485 bridges

### Connection Strategies
- **Persistent**: Reuses connections with health monitoring and age-based reconnection
- **Per-request**: Uses fresh connection for each request (slower but more reliable)

### Error Handling
- **Graceful degradation**: Continues processing even when some commands fail
- **Comprehensive error reporting**: Clear error messages in JSON output
- **Resource cleanup**: Ensures connections are always closed properly

### JSON Output
- **Complete metadata**: Includes TCP host/port and timing information
- **Structured data**: Well-organized, JSON-serializable response format
- **Error integration**: Errors are included in JSON structure for programmatic handling

## Test Coverage

The demo tests provide comprehensive coverage of:
- ✅ All four BMS read commands (voltage, current, capacity, serial)
- ✅ Connection establishment and cleanup
- ✅ Error handling and recovery
- ✅ JSON serialization and formatting
- ✅ Summary calculations
- ✅ Logging configuration
- ✅ Transport reliability features
- ✅ Both connection strategies
- ✅ Integration with fake BMS server
- ✅ Timeout and error scenarios

## Expected Results

When running against a real BMS or fake server, you should see:
- Successful collection of all available data
- Proper JSON formatting with metadata
- Graceful handling of any connection issues
- Automatic retry and recovery from temporary failures
- Clean resource cleanup regardless of success/failure

These tests demonstrate that the enhanced main.py and transport layer provide robust, reliable communication with BMS devices even in challenging network conditions.
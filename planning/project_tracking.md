# Orion 1000 BMS Implementation Progress Checklist

This document tracks the completion status of each phase and step outlined in the implementation plan section of the file docs/project_plan.md.

## Phase 0 – Bootstrap & tooling

- [x] APPROVED: Create `src/` layout shown above
- [x] APPROVED: Configure `pyproject.toml` with build settings, dev deps, and tool configurations
- [x] APPROVED: Add `README.md` with minimal example and `LICENSE`

### Affected Files:

- CHANGELOG.md
- LICENSE
- README.md
- pyproject.toml
- src/orion1000_bms/**init**.py
- src/orion1000_bms/commands/**init**.py
- src/orion1000_bms/protocol/**init**.py
- src/orion1000_bms/py.typed
- src/orion1000_bms/transport/**init**.py
- tests/conftest.py

## Phase 1 – Protocol constants & checksum

- [x] APPROVED: Create `protocol/constants.py` with START, END, PRODUCT_ID_DEFAULT
- [x] APPROVED: Implement `xor_checksum()` function in `protocol/codec.py`
- [x] APPROVED: Add unit tests for checksum examples from spec

### Affected Files:

- src/orion1000_bms/protocol/codec.py
- src/orion1000_bms/protocol/constants.py
- tests/unit/test_checksum.py

## Phase 2 – Frame type & encode/decode

- [x] APPROVED: Create `Frame` dataclass in `protocol/frame.py` with all fields
- [x] APPROVED: Implement `to_bytes()` method for frame encoding
- [x] APPROVED: Implement `from_bytes()` classmethod for frame decoding with validation
- [x] APPROVED: Add `build_frame()` and `decode()` functions to `protocol/codec.py`
- [x] APPROVED: Add tests for round-trip encode/decode and boundary checks

### Affected Files:

- src/orion1000_bms/protocol/codec.py
- src/orion1000_bms/protocol/frame.py
- tests/unit/test_codec.py
- tests/unit/test_constants.py
- tests/unit/test_frame.py

## Phase 3 – Transport (TCP)

- [x] APPROVED: Define `AbstractTransport` Protocol in `transport/base.py`
- [x] APPROVED: Implement sync TCP transport in `transport/tcp.py` with socket handling
- [x] APPROVED: Implement deterministic read strategy (two-phase read with end-byte verification)
- [x] APPROVED: Add tests with fake TCP server for canned responses

### Affected Files:

- src/orion1000_bms/transport/base.py
- src/orion1000_bms/transport/tcp.py
- tests/integration/fakes/fake_bms_server.py
- tests/integration/test_tcp_transport.py

## Phase 4 – Exceptions & logging

- [x] APPROVED: Create exception hierarchy in `exceptions.py`
- [x] APPROVED: Implement logger factory in `logging.py` with hex dump support

### Affected Files:

- src/orion1000_bms/exceptions.py
- src/orion1000_bms/logging.py
- src/orion1000_bms/protocol/frame.py
- src/orion1000_bms/transport/tcp.py
- tests/unit/test_exceptions.py
- tests/unit/test_logging.py

## Phase 5 – Commands & registry (initial set)

- [x] APPROVED: Define `BaseCommand`/`BaseResponse` Protocols in `commands/base.py`
- [x] APPROVED: Create `CommandId` enum and registry in `commands/registry.py`
- [x] APPROVED: Implement `read_total_voltage.py` command
- [x] APPROVED: Implement `read_cell_voltage.py` command (single-cell and multi-frame)
- [x] APPROVED: Implement `read_current.py` command
- [x] APPROVED: Add tests using example frames from spec as golden vectors

### Affected Files:

- src/orion1000_bms/commands/base.py
- src/orion1000_bms/commands/read_cell_voltage.py
- src/orion1000_bms/commands/read_current.py
- src/orion1000_bms/commands/read_total_voltage.py
- src/orion1000_bms/commands/registry.py
- tests/integration/data/frames/golden_frames.py
- tests/integration/test_golden_frames.py
- tests/unit/test_commands.py

## Phase 6 – Client APIs (sync)

- [x] PENDING_APPROVAL: Implement `BmsClient` with generic `request()` method
- [x] PENDING_APPROVAL: Add helper methods for common operations
- [x] PENDING_APPROVAL: Enforce ≥200ms spacing between requests with configurable overrides

### Affected Files:

- src/orion1000_bms/**init**.py
- src/orion1000_bms/client.py
- tests/integration/test_client_integration.py
- tests/unit/test_client.py

## Phase 7 – CLI (optional but handy)

- [x] SKIPPED: Create Typer-based CLI in `cli.py`
- [x] SKIPPED: Add `bms status` command
- [x] SKIPPED: Add `bms raw` command for hex frame sending
- [x] SKIPPED: Add `bms cells` command

## Phase 8 – Testing strategy

- [ ] TODO: Add unit tests for checksum, frame parsing, command parsers
- [ ] TODO: Create golden hex fixtures from spec
- [ ] TODO: Add property-based tests with hypothesis (optional)
- [ ] TODO: Implement `fake_bms_server.py` for integration tests

## Phase 9 – Ergonomics & DX

- [ ] TODO: Ensure minimal runtime dependencies
- [ ] TODO: Add rich type hints and `slots=True` for dataclasses
- [ ] TODO: Configure ruff and pyright/mypy for clean linting and type checking
- [ ] TODO: Add `py.typed` marker for typing consumers

## Phase 10 – Future extensions

- [ ] TODO: Design serial transport interface using pyserial
- [ ] TODO: Plan streaming/subscribe API for periodic polling
- [ ] TODO: Add metrics hooks for command durations and error counts
- [ ] TODO: Design config command support with safety guardrails

## Acceptance Checklist

- [ ] TODO: Encode/decode round-trips for all initial commands
- [ ] TODO: Checksum unit tests cover spec examples
- [ ] TODO: Transport integration test passes against fake TCP server
- [ ] TODO: Enforced ≥200ms spacing between requests
- [ ] TODO: Golden fixtures live in `tests/integration/data/frames/`
- [ ] TODO: CLI can send raw frame and print hex dump
- [ ] TODO: Type-check clean, ruff clean, tests green

## Unplanned work

- Updated test files to expect new exception types (FrameError, ChecksumError, TransportError) instead of ValueError and generic exceptions.
- Added pytest markers (@pytest.mark.phase1, @pytest.mark.phase2, etc.) to all test functions to identify which implementation phase they cover.
- Fixed test compatibility issues after implementing Phase 4 exception hierarchy.
- Updated protocol implementation to align with corrected English translation of Chinese specification.
- Fixed checksum calculation to exclude Product ID and Address bytes as per updated specification.
- Updated command structure to use Command High (0xFF) + Command Low format instead of combined command IDs.
- Implemented new command set: voltage request, current/status request, capacity/status request, serial number request, and MOS control commands.
- Updated all response data structures to match detailed layouts in updated specification.
- Removed old command implementations (read_total_voltage, read_current, read_cell_voltage) and replaced with specification-compliant commands.
- Updated client API to provide both new methods and backward-compatible convenience methods.
- Refactored response parsing logic to remove hard-coded payload length expectations and implement proper length-based parsing using the length byte (byte 4) from the protocol specification.
- Updated command modules to reflect corrected protocol specification with variable-length responses, bitfield parsing, tag-based data structures, and proper temperature conversion.
- Created common parsing utilities for temperature conversion, bitfield extraction, and tag-based parsing.
- Enhanced base response class with variable-length payload validation.
- Completely rewrote voltage, current status, and capacity status response parsing to match updated specification.
- Fixed MOS control response parsing to handle fixed acknowledgment frame format.
- Added comprehensive tests for new parsing utilities and updated command logic.
- Fixed TCP transport test hanging issue by adding proper cleanup with try/finally blocks and context manager support.
- Enhanced TcpTransport with context manager protocol for automatic resource cleanup.
- Improved \_read_exact method to detect broken connections and avoid infinite loops.
- Fixed fake BMS server to include command bytes in response payloads as expected by parsers.
- Fixed client integration tests by correcting fake server payload format - removed duplicate command bytes since client adds them automatically.
- Updated TCP transport test expectations to match corrected payload sizes.
- Enhanced ResponseBase with metadata fields (TCP host/port, request/response timestamps) and JSON serialization support.
- Updated BmsClient to capture and set response metadata with timing information.
- Completely rewrote main.py to test all four read-only commands and output complete JSON-formatted responses.
- Fixed capacity status request minimum payload length to match actual BMS response (49 bytes vs 50).
- Validated all four commands work correctly against real Orion 1000 BMS hardware.
- Enhanced TCP transport with connection health monitoring, automatic reconnection, and retry logic to eliminate intermittent timeout issues.
- Added configurable connection strategies (persistent vs per-request) and enhanced buffer management for TCP-to-RS485 bridges.
- Implemented connection age-based reconnection, enhanced error detection, and improved resource cleanup.
- Created comprehensive demo test suite in demo/ directory with unit tests, integration tests, and reliability tests covering all main.py functionality.
- Updated main.py to use per-request connection strategy with enhanced reliability settings for maximum robustness.

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

- [x] PENDING_APPROVAL: Create `Frame` dataclass in `protocol/frame.py` with all fields
- [x] PENDING_APPROVAL: Implement `to_bytes()` method for frame encoding
- [x] PENDING_APPROVAL: Implement `from_bytes()` classmethod for frame decoding with validation
- [x] PENDING_APPROVAL: Add `build_frame()` and `decode()` functions to `protocol/codec.py`
- [x] PENDING_APPROVAL: Add tests for round-trip encode/decode and boundary checks

### Affected Files:

- src/orion1000_bms/protocol/codec.py
- src/orion1000_bms/protocol/frame.py
- tests/unit/test_codec.py
- tests/unit/test_constants.py
- tests/unit/test_frame.py

## Phase 3 – Transport (TCP)

- [ ] TODO: Define `AbstractTransport` Protocol in `transport/base.py`
- [ ] TODO: Implement sync TCP transport in `transport/tcp.py` with socket handling
- [ ] TODO: Add deterministic read strategy (two-phase read with end-byte verification)
- [ ] TODO: Add tests with fake TCP server for canned responses

## Phase 4 – Exceptions & logging

- [ ] TODO: Create exception hierarchy in `exceptions.py`
- [ ] TODO: Implement logger factory in `logging.py` with hex dump support

## Phase 5 – Commands & registry (initial set)

- [ ] TODO: Define `BaseCommand`/`BaseResponse` Protocols in `commands/base.py`
- [ ] TODO: Create `CommandId` enum and registry in `commands/registry.py`
- [ ] TODO: Implement `read_total_voltage.py` command
- [ ] TODO: Implement `read_cell_voltage.py` command (single-cell and multi-frame)
- [ ] TODO: Implement `read_current.py` command
- [ ] TODO: Add tests using example frames from spec as golden vectors

## Phase 6 – Client APIs (sync)

- [ ] TODO: Implement `BmsClient` with generic `request()` method
- [ ] TODO: Add helper methods for common operations
- [ ] TODO: Enforce ≥200ms spacing between requests with configurable overrides

## Phase 7 – CLI (optional but handy)

- [ ] TODO: Create Typer-based CLI in `cli.py`
- [ ] TODO: Add `bms status` command
- [ ] TODO: Add `bms raw` command for hex frame sending
- [ ] TODO: Add `bms cells` command

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

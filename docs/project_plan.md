# Orion 1000 BMS – Python Package Structure & Implementation Plan

This document describes the recommended structure and step‑by‑step plan to implement a typed, testable Python 3.12 package for communicating with the Orion 1000 BMS over RS‑485 via a TCP device server.

> Design goals
>
> - Clean separation of concerns (transport ↔ framing/codec ↔ commands ↔ client).
> - Single source of truth for frame layout and checksum.
> - Easy to add commands by implementing small request/response classes.
> - Sync and async clients share the same parsing/encoding logic.
> - Robust I/O over TCP with per‑request serialization, timeouts, and retries.

---

## 1) Package layout (src/ structure)

```
src/
  orion1000_bms/
    __init__.py
    exceptions.py            # Typed exception hierarchy
    types.py                 # TypedDicts, enums, Literals shared across modules
    logging.py               # Logger factory/helper (no global config)

    transport/
      __init__.py
      base.py                # AbstractTransport (send_request -> bytes)
      tcp.py                 # Sync TCP transport (socket)
      tcp_async.py           # Async TCP transport (asyncio streams)
      utils.py               # Reconnect/backoff, keepalive, small helpers

    protocol/
      __init__.py
      constants.py           # START=0xEA, END=0xF5, PRODUCT_ID=0xD1, etc.
      frame.py               # Frame dataclass + from_bytes/to_bytes + validation
      codec.py               # build_frame()/decode() + checksum + hex utils
      helpers.py             # Bounds checks, formatting, small pure helpers

    commands/
      __init__.py
      base.py                # BaseCommand/BaseResponse Protocols/ABCs
      registry.py            # CommandId Enum + CommandSpec registry
      read_total_voltage.py  # Example read command
      read_cell_voltage.py   # Example read command (single or multi‑frame)
      read_current.py        # Example read command
      # add additional read/write commands here as files

    client.py                # BmsClient (sync)
    client_async.py          # BmsClientAsync (async)
    polling.py               # Optional periodic polling helpers
    cli.py                   # Typer CLI (optional user tool)

tests/
  unit/
    test_checksum.py
    test_frame.py
    test_codec.py
    test_commands_*.py
  integration/
    fakes/
      fake_bms_server.py    # Deterministic TCP fake
    data/frames/            # Golden hex fixtures captured from docs/hardware
  conftest.py

pyproject.toml               # build, ruff, pytest, pyright/mypy, typing
README.md                    # quickstart, examples
CHANGELOG.md                 # semantic versioning history
LICENSE
```

---

## 2) Responsibilities by layer

### Transport

- Contract: `send_request(payload: bytes, *, timeout: float | None) -> bytes` returns the **raw response bytes**.
- TCP options: TCP_NODELAY, keepalive; configurable connect/read/write timeouts.
- Per‑connection lock to guarantee **one in‑flight request at a time** (RS‑485 is half‑duplex; treat TCP bridge as serialized).
- Reconnect with jittered backoff on `ConnectionError`.
- Read strategy supports:
  1. **Two‑phase read** (read fixed header, then compute remaining length), and
  2. **Until end‑byte** safety check.

### Protocol (framing + validation)

- Frame layout per spec:
  `[Start][ProductId][Address][DataLen][CmdHi][CmdLo][Data...][Checksum][End]`.
- `DataLen` is the length from **CmdHi** through **Data** (i.e., includes the 2 command bytes plus data bytes).
- Checksum is XOR of all bytes **from ProductId through Data**.
- Strict validation: start byte (0xEA), product id (0xD1 by default), end byte (0xF5), length bounds, checksum.
- Multi‑frame support: some commands (e.g., all‑cell voltages) may require multiple frames; expose an iterator/collector.

### Commands (typed models)

- Each command provides:
  - `command_id: CommandId` (16‑bit combining hi/lo),
  - `to_payload() -> bytes` for request body (often empty for reads),
  - `from_payload(payload: bytes) -> Response` to parse the response data.
- Central registry maps command id → request/response types so the client can be generic.

### Clients

- `BmsClient` and `BmsClientAsync` expose ergonomic methods (e.g., `read_total_voltage()`).
- They build/encode a frame, call the transport, decode/validate, and dispatch to the response parser.
- Respect an inter‑request delay (≥ 200 ms) and command‑specific overrides.

---

## 3) Step‑by‑step implementation plan

### Phase 0 – Bootstrap & tooling

1. Create `src/` layout shown above.
2. Configure `pyproject.toml`:
   - Build: `setuptools>=68` (or `hatchling`) and `python = ">=3.12"`.
   - Dev deps: `pytest`, `hypothesis` (optional), `ruff`, `mypy` or `pyright`, `typer[all]` (optional), `coverage`.
   - Ruff and type‑checker settings (strict but practical).
3. Add `README.md` with a minimal example; add `LICENSE`.

### Phase 1 – Protocol constants & checksum

- `protocol/constants.py`
  - `START = 0xEA`, `END = 0xF5`, `PRODUCT_ID_DEFAULT = 0xD1`.
- `protocol/codec.py`
  - `def xor_checksum(data: bytes) -> int:` (XOR of ProductId..Data).
  - Unit tests for checksum examples from the spec.

### Phase 2 – Frame type & encode/decode

- `protocol/frame.py`
  - Frozen `@dataclass(slots=True)` with fields: `start, product_id, address, data_len, cmd_hi, cmd_lo, payload, checksum, end`.
  - `to_bytes()` builds the frame and computes checksum.
  - `@classmethod from_bytes(raw: bytes) -> Frame` validates markers, `data_len`, checksum; returns structured data.
- `protocol/codec.py`
  - `build_frame(product_id: int, address: int, cmd_hi: int, cmd_lo: int, payload: bytes) -> bytes`.
  - `decode(raw: bytes) -> Frame` delegating to `Frame.from_bytes`.
- Tests: round‑trip encode/decode; boundary checks (short frames, wrong markers, bad checksum, length mismatch).

### Phase 3 – Transport (TCP)

- `transport/base.py` defines `AbstractTransport` Protocol with `open_if_needed()`, `close()`, `send_request(...)`.
- `transport/tcp.py` (sync): `socket.create_connection`, locks, timeouts, deterministic reads:
  1. Read 1 byte (start), then next 4 bytes to reach `data_len` field, or read a fixed header size.
  2. Parse header to compute remaining (2 cmd bytes + data bytes) + checksum + end.
  3. Read remainder; verify final end byte present.
- `transport/tcp_async.py`: mirror using `asyncio.open_connection` + `asyncio.Lock`.
- Tests: fake TCP server responds with canned frames for known commands.

### Phase 4 – Exceptions & logging

- `exceptions.py`:
  - `TransportError`, `TimeoutError`, `ChecksumError`, `FrameError`, `ProtocolError`, `UnsupportedCommandError`.
- `logging.py`:
  - `get_logger(__name__)` with library‑friendly defaults.
  - Hex dumps for TX/RX at debug level (never redact—frames are your truth source).

### Phase 5 – Commands & registry (initial set)

- `commands/base.py` defines `BaseCommand` / `BaseResponse` Protocols and a `CommandSpec` dataclass.
- `commands/registry.py`:
  - `class CommandId(IntEnum)` combining hi/lo: e.g., `READ_TOTAL_VOLTAGE = 0x0300`, `READ_CELL_VOLTAGE = 0x0301`, `READ_CURRENT = 0x0302`, etc.
  - `COMMANDS: dict[CommandId, CommandSpec]` mapping to request/response types.
- Implement initial commands based on the spec:
  - `read_total_voltage.py`
  - `read_cell_voltage.py` (single‑cell index or multi‑frame all‑cells collector)
  - `read_current.py`
- Tests use example frames from the spec as golden vectors.

### Phase 6 – Client APIs (sync + async)

- `client.py` exposes:
  - `request(self, req: BaseCommand, *, timeout: float | None = None) -> BaseResponse`
  - Helper methods: `read_total_voltage()`, `read_current()`, `read_cell_voltage(cell: int)`.
  - Enforce ≥ 200 ms spacing between requests (configurable); allow per‑command overrides.
- `client_async.py` mirrors the API with `async`/`await` and `asyncio.Lock`.

### Phase 7 – CLI (optional but handy)

- `cli.py` with [Typer](https://typer.tiangolo.com/):
  - `bms status --host 192.168.1.50 --port 4001 --address 0x01`
  - `bms raw --hex "EA D1 01 02 03 00 D2 F5"`
  - `bms cells --all`

### Phase 8 – Testing strategy

- **Unit**: checksum, frame parsing, command parsers (edge cases: min/max lengths, invalid markers).
- **Golden**: hex fixtures from the spec for deterministic parsing tests.
- **Property** (optional): fuzz payload lengths and checksum correctness with `hypothesis`.
- **Integration**: `tests/integration/fakes/fake_bms_server.py` that validates incoming frames and returns canned responses per command id. Run client APIs against it.

### Phase 9 – Ergonomics & DX

- Minimal runtime deps: stdlib + optional Typer. Keep install footprint small.
- Rich type hints and `slots=True` for dataclasses; `__bytes__()` where natural.
- `ruff` for lint, `pyright` for types. `pytest -q` as default test target.
- Consider `py.typed` and `py.3.12` markers for typing consumers.

### Phase 10 – Future extensions

- Serial transport using `pyserial` (swap `TcpTransport` with `SerialTransport`).
- Streaming/subscribe API for periodic polling, with backpressure.
- Metrics hooks (callbacks) for command durations and error counts.
- Config command support with guardrails (write operations are dangerous).

---

## 4) Code scaffolds (illustrative)

### Command id & registry

```python
# src/orion1000_bms/commands/registry.py
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol, Type

class CommandId(IntEnum):
    READ_TOTAL_VOLTAGE = 0x0300
    READ_CELL_VOLTAGE  = 0x0301
    READ_CURRENT       = 0x0302

class BaseCommand(Protocol):
    command_id: CommandId
    address: int
    def to_payload(self) -> bytes: ...

class BaseResponse(Protocol):
    @classmethod
    def from_payload(cls, payload: bytes) -> "BaseResponse": ...

@dataclass(slots=True, frozen=True)
class CommandSpec:
    req: Type[BaseCommand]
    resp: Type[BaseResponse]

COMMANDS: dict[CommandId, CommandSpec] = {}
```

### Frame & codec contracts

```python
# src/orion1000_bms/protocol/constants.py
START: int = 0xEA
END: int = 0xF5
PRODUCT_ID_DEFAULT: int = 0xD1
```

```python
# src/orion1000_bms/protocol/frame.py
from __future__ import annotations
from dataclasses import dataclass

a = dataclass(slots=True, frozen=True)
class Frame:
    start: int
    product_id: int
    address: int
    data_len: int
    cmd_hi: int
    cmd_lo: int
    payload: bytes
    checksum: int
    end: int

    def to_bytes(self) -> bytes: ...
    @classmethod
    def from_bytes(cls, raw: bytes) -> "Frame": ...
```

### Sync client outline

```python
# src/orion1000_bms/client.py
from __future__ import annotations
import threading
from .transport.base import AbstractTransport
from .protocol import codec
from .commands.registry import CommandId, COMMANDS, BaseCommand, BaseResponse

class BmsClient:
    def __init__(self, transport: AbstractTransport, *, product_id: int, address: int, min_spacing_s: float = 0.2):
        self._t = transport
        self._product_id = product_id
        self._address = address
        self._lock = threading.Lock()
        self._min_spacing_s = min_spacing_s
        self._last_ts = 0.0

    def request(self, req: BaseCommand, *, timeout: float | None = None) -> BaseResponse:
        # enforce one-in-flight and min spacing
        ...
```

---

## 5) Acceptance checklist

- [ ] Encode/decode round‑trips for all initial commands.
- [ ] Checksum unit tests cover spec examples.
- [ ] Transport integration test passes against fake TCP server.
- [ ] Enforced ≥ 200 ms spacing between requests.
- [ ] Golden fixtures live in `tests/integration/data/frames/`.
- [ ] CLI can send a raw frame and print a hex dump.
- [ ] Type‑check clean; ruff clean; tests green.

---

## 6) Quickstart (once implemented)

```bash
pip install -e .[dev]
pytest -q
python -m orion1000_bms.cli status --host 192.168.1.50 --port 4001 --address 0x01
```

> For details on frame layout and the initial command set, refer to `docs/protocol_spec_english.md`.

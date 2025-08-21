import time
import logging
import serial

START = 0xEA
END = 0xF5
PID = 0xD1
CMDH = 0xFF


def xorf(b: bytes) -> int:
    v = 0
    for x in b:
        v ^= x
    return v


def read_exact(ser: serial.Serial, n: int, *, timeout_s: float = 1.0) -> bytes:
    """Read exactly n bytes or raise TimeoutError."""
    end_by = time.monotonic() + timeout_s
    buf = bytearray()
    while len(buf) < n:
        if time.monotonic() > end_by:
            raise TimeoutError(f"Timeout reading {n} bytes (got {len(buf)})")
        chunk = ser.read(n - len(buf))
        if chunk:
            buf.extend(chunk)
        else:
            # small yield; keeps CPU low without affecting inter-request pacing
            time.sleep(0.005)
    return bytes(buf)


def read_frame(
    ser: serial.Serial,
    *,
    expect_addr: int | None = 0x01,
    header_timeout_s: float = 1.0,
    payload_timeout_s: float = 1.0,
) -> bytes:
    """Read one frame: [EA D1 addr len] + len bytes; validate end & checksum."""
    # Read header
    logging.debug("Waiting for frame header bytes...")
    hdr = read_exact(ser, 4, timeout_s=header_timeout_s)
    if hdr[0] != START:
        raise ValueError(f"Bad start byte: {hdr[0]:#04x}")
    if hdr[1] != PID:
        raise ValueError(f"Unexpected product id: {hdr[1]:#04x}")
    if expect_addr is not None and hdr[2] != expect_addr:
        raise ValueError(
            f"Unexpected addr: {hdr[2]:#04x} (expected {expect_addr:#04x})"
        )

    length = hdr[3]
    if length < 4:
        raise ValueError(f"Length too small to contain cmd/cksum/end: {length}")

    payload = read_exact(ser, length, timeout_s=payload_timeout_s)
    if payload[-1] != END:
        raise ValueError("Missing or incorrect end byte 0xF5")

    # checksum over [Length + payload_without_cksum_end]
    checksum = payload[-2]
    if xorf(bytes([length]) + payload[:-2]) != checksum:
        raise ValueError("Checksum mismatch")

    return hdr + payload


def main() -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    host = "192.168.99.94"
    port = 26
    url = f"socket://{host}:{port}"

    # Exact test frame from spec: EA D1 01 04 FF 02 F9 F5
    request = bytes([0xEA, 0xD1, 0x01, 0x04, 0xFF, 0x02, 0xF9, 0xF5])

    logging.debug("Opening %s", url)
    ser = serial.serial_for_url(
        url,
        timeout=3.0,  # per read timeout
        inter_byte_timeout=0.2,  # helps with TCP bridges
        write_timeout=1.0,
    )

    try:
        # Clear any stale bytes
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        logging.debug("Sending: %s", request.hex(" ").upper())
        ser.write(request)
        ser.flush()

        # Read deterministically (no polling loops)
        frame = read_frame(
            ser, expect_addr=0x01, header_timeout_s=3.5, payload_timeout_s=3.5
        )
        logging.info("Response (%d bytes): %s", len(frame), frame.hex(" ").upper())

        # Optional: decode quick fields
        start, pid, addr, length = frame[0], frame[1], frame[2], frame[3]
        cmd_high = frame[4]
        cmd_low = frame[5]
        checksum = frame[-2]
        endb = frame[-1]
        logging.debug(
            "Parsed: start=%#04X pid=%#04X addr=%#04X len=%d cmd_high=%#04X cmd_low=%#04X checksum=%#04X end=%#04X",
            start,
            pid,
            addr,
            length,
            cmd_high,
            cmd_low,
            checksum,
            endb,
        )

    except Exception as e:
        logging.error("Communication failed: %s", e)
    finally:
        # Respect inter-scan spacing before any subsequent request
        time.sleep(0.20)  # ≥200 ms per spec
        ser.close()
        logging.debug("Closed connection")


if __name__ == "__main__":
    main()

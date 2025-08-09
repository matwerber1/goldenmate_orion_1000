import logging, os, json
from dataclasses import asdict

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "DEBUG").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)

from orion1000_bms import Orion1000BMS, BMSConfig


if __name__ == "__main__":

    cfg = BMSConfig(host="192.168.99.137", port=26, addr=0x01)
    bms = Orion1000BMS(cfg)
    v = bms.read_voltage()
    print(json.dumps(asdict(v), indent=2))

    cs = bms.read_current_status()
    print(json.dumps(asdict(cs), indent=2))

    cap = bms.read_capacity()
    print(json.dumps(asdict(cap), indent=2))

    bid = bms.read_battery_id()
    print(json.dumps(asdict(bid), indent=2))

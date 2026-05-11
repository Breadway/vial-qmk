#!/usr/bin/env python3
import argparse
import json
import time

try:
    import hid
except ImportError as exc:
    raise SystemExit("Missing dependency: python3 -m pip install --user hid") from exc


RAW_USAGE_PAGE = 0xFF60
RAW_USAGE = 0x61
REPORT_ID_LAYER_STATE = 0x01
REPORT_LEN = 32

LAYER_NAMES = {
    0: "QWERTY",
    1: "SYMB",
    2: "NAV",
    3: "ADJUST",
}


def open_device(vendor_id: int, product_id: int):
    devices = [
        dev
        for dev in hid.enumerate(vendor_id, product_id)
        if dev.get("usage_page") == RAW_USAGE_PAGE and dev.get("usage") == RAW_USAGE
    ]
    if not devices:
        raise SystemExit("No matching raw HID device found")
    return hid.Device(path=devices[0]["path"])


def read_u32_le(buf, start):
    return int.from_bytes(bytes(buf[start:start + 4]), "little")


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit Redox layer state as JSON lines")
    parser.add_argument("--vid", type=lambda s: int(s, 0), default=0x4D44)
    parser.add_argument("--pid", type=lambda s: int(s, 0), default=0x5244)
    args = parser.parse_args()

    dev = open_device(args.vid, args.pid)

    try:
        while True:
            data = dev.read(REPORT_LEN, timeout=1000)
            if not data:
                continue

            if data[0] != REPORT_ID_LAYER_STATE:
                continue

            effective = data[1]
            active = data[2]
            default = data[3]
            layer_state = read_u32_le(data, 4)
            default_state = read_u32_le(data, 8)

            payload = {
                "timestamp": time.time(),
                "report_id": data[0],
                "layer": effective,
                "active_layer": active,
                "default_layer": default,
                "layer_name": LAYER_NAMES.get(effective, f"L{effective}"),
                "layer_state": layer_state,
                "default_layer_state": default_state,
            }
            print(json.dumps(payload), flush=True)
    except KeyboardInterrupt:
        return 0
    finally:
        dev.close()


if __name__ == "__main__":
    raise SystemExit(main())

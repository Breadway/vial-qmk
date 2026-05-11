#!/usr/bin/env python3
import argparse
import sys

try:
    import hid
except ImportError as exc:
    raise SystemExit("Missing dependency: python3 -m pip install --user hid") from exc


RAW_USAGE_PAGE = 0xFF60
RAW_USAGE = 0x61
REPORT_ID_LAYER_STATE = 0x01
REPORT_LEN = 32


def open_device(vendor_id: int, product_id: int):
    devices = [
        dev
        for dev in hid.enumerate(vendor_id, product_id)
        if dev.get("usage_page") == RAW_USAGE_PAGE and dev.get("usage") == RAW_USAGE
    ]
    if not devices:
        raise SystemExit("No matching raw HID device found")
    return hid.Device(path=devices[0]["path"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Listen for Redox layer reports over raw HID")
    parser.add_argument("--vid", type=lambda s: int(s, 0), default=0x4D44)
    parser.add_argument("--pid", type=lambda s: int(s, 0), default=0x5244)
    args = parser.parse_args()

    dev = open_device(args.vid, args.pid)
    print("Listening for layer reports. Press layer keys on the flashed half.")

    try:
        while True:
            data = dev.read(REPORT_LEN, timeout=1000)
            if not data:
                continue

            if data[0] != REPORT_ID_LAYER_STATE:
                print("report:", data)
                continue

            effective = data[1]
            active = data[2]
            default = data[3]
            layer_state = int.from_bytes(bytes(data[4:8]), "little")
            default_state = int.from_bytes(bytes(data[8:12]), "little")

            print(
                f"layer={effective} active={active} default={default} "
                f"layer_state=0x{layer_state:08x} default_layer_state=0x{default_state:08x}"
            )
    except KeyboardInterrupt:
        return 0
    finally:
        dev.close()


if __name__ == "__main__":
    raise SystemExit(main())

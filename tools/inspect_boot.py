#!/usr/bin/env python3
"""Inspect an unpacked Android boot container, without invoking flash tools.

Supports boot header versions 0 through 4. Vendor boot containers and MediaTek
wrappers must be inspected separately; an embedded magic is not auto-selected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def inspect(data):
    def u32(offset):
        if offset + 4 > len(data):
            raise ValueError("truncated boot header")
        return struct.unpack_from("<I", data, offset)[0]

    def u64(offset):
        if offset + 8 > len(data):
            raise ValueError("truncated boot header")
        return struct.unpack_from("<Q", data, offset)[0]

    def string(start, size):
        return data[start:start + size].split(b"\0", 1)[0].decode("utf-8", "replace")

    def align(value, page):
        return (value + page - 1) // page * page

    if data[:8] != b"ANDROID!":
        raise ValueError("missing ANDROID! magic at offset zero; wrapped/vendor images are unsupported")
    version = u32(40)
    if version > 4:
        raise ValueError(f"unsupported boot header version {version}")
    minimum = [1632, 1648, 1660, 1580, 1584][version]
    if len(data) < minimum:
        raise ValueError("truncated boot header")
    segments = []

    def segment(name, offset, size):
        if not size:
            return
        if offset < page or offset + size > len(data):
            raise ValueError(f"{name} extends outside the image or overlaps the header")
        for other in segments:
            if offset < other["offset"] + other["size"] and other["offset"] < offset + size:
                raise ValueError(f"{name} overlaps {other['name']}")
        segments.append({"name": name, "offset": offset, "size": size,
                         "sha256": hashlib.sha256(data[offset:offset + size]).hexdigest()})

    result = {"header_version": version, "image_size": len(data),
              "sha256": hashlib.sha256(data).hexdigest()}
    if version <= 2:
        page = u32(36)
        if page < minimum or page > 65536 or page & (page - 1):
            raise ValueError(f"invalid page size {page}")
        kernel_size, ramdisk_size, second_size = u32(8), u32(16), u32(24)
        result.update(page_size=page, name=string(48, 16),
                      cmdline=string(64, 512) + string(608, 1024),
                      kernel_addr=u32(12), ramdisk_addr=u32(20),
                      second_addr=u32(28), tags_addr=u32(32))
        cursor = page
        for name, size in [("kernel", kernel_size), ("ramdisk", ramdisk_size), ("second", second_size)]:
            segment(name, cursor, size)
            cursor += align(size, page)
        if version >= 1:
            header_size = u32(1644)
            if header_size < minimum or header_size > page:
                raise ValueError("invalid declared header size")
            result["header_size"] = header_size
            recovery_size, recovery_offset = u32(1632), u64(1636)
            if recovery_size:
                if recovery_offset != cursor:
                    raise ValueError("unexpected recovery DTBO offset")
                segment("recovery_dtbo", recovery_offset, recovery_size)
                cursor += align(recovery_size, page)
        if version == 2:
            result["dtb_addr"] = u64(1652)
            segment("dtb", cursor, u32(1648))
    else:
        page = 4096
        header_size = u32(20)
        if header_size < minimum or header_size > page:
            raise ValueError("invalid declared header size")
        result.update(page_size=page, header_size=header_size, cmdline=string(44, 1536))
        kernel_size, ramdisk_size = u32(8), u32(12)
        segment("kernel", page, kernel_size)
        cursor = page + align(kernel_size, page)
        segment("ramdisk", cursor, ramdisk_size)
        cursor += align(ramdisk_size, page)
        if version == 4:
            segment("boot_signature", cursor, u32(1580))
        result["note"] = "DTB, vendor ramdisk and boot addresses require a separate vendor_boot image"
    result["segments"] = segments
    result["verification"] = "structural inspection only; signatures and bootability are not verified"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--extract", type=Path, help="create a NEW directory for component copies and report")
    args = parser.parse_args()
    try:
        data = args.image.read_bytes()
        report = inspect(data)
        if args.extract:
            args.extract.mkdir(parents=True, exist_ok=False)
            for item in report["segments"]:
                (args.extract / (item["name"] + ".bin")).write_bytes(
                    data[item["offset"]:item["offset"] + item["size"]])
            (args.extract / "boot.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    except (OSError, ValueError) as exc:
        print(f"inspect_boot: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

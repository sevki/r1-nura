import importlib.util
from pathlib import Path
import struct
import unittest
import json
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location(
    "inspect_boot", Path(__file__).resolve().parents[1] / "tools/inspect_boot.py")
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)


def fixture(version):
    page = 2048 if version <= 2 else 4096
    data = bytearray(page * 5)
    data[:8] = b"ANDROID!"
    def put(offset, value):
        struct.pack_into("<I", data, offset, value)
    put(40, version)
    put(8, 16)
    put(16 if version <= 2 else 12, 8)
    if version <= 2:
        put(36, page)
        data[64:68] = b"test"
        if version >= 1:
            put(1644, 1648 if version == 1 else 1660)
            put(1632, 4)
            struct.pack_into("<Q", data, 1636, page * 3)
        if version == 2:
            put(1648, 4)
    else:
        put(20, 1580 if version == 3 else 1584)
        if version == 4:
            put(1580, 4)
    return data


class InspectTests(unittest.TestCase):
    def test_all_supported_layouts(self):
        for version in range(5):
            with self.subTest(version=version):
                report = boot.inspect(fixture(version))
                self.assertEqual(report["header_version"], version)
                self.assertEqual(report["segments"][0]["name"], "kernel")
                expected = {0: 2, 1: 3, 2: 4, 3: 2, 4: 3}[version]
                self.assertEqual(len(report["segments"]), expected)
                self.assertEqual(report["segments"][1]["offset"], report["page_size"] * 2)

    def test_cli_extract_and_refuse_existing_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'boot.img'
            data = fixture(2)
            data[2048:2064] = b'kernel-content!!'
            source.write_bytes(data)
            target = root / 'extracted'
            command = [sys.executable, str(Path(boot.__file__)), str(source),
                       '--extract', str(target)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((target / 'kernel.bin').read_bytes(), b'kernel-content!!')
            self.assertEqual(json.loads((target / 'boot.json').read_text()),
                             json.loads(result.stdout))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((target / 'kernel.bin').read_bytes(), b'kernel-content!!')
            self.assertEqual(source.read_bytes(), data)

    def test_signature_outside_image(self):
        data = fixture(4)
        struct.pack_into('<I', data, 1580, len(data))
        with self.assertRaises(ValueError):
            boot.inspect(data)

    def test_truncation(self):
        for size in (0, 8, 100, 1631, 2050):
            with self.subTest(size=size), self.assertRaises(ValueError):
                boot.inspect(fixture(0)[:size])

    def test_invalid_page_size(self):
        data = fixture(0)
        struct.pack_into("<I", data, 36, 3000)
        with self.assertRaises(ValueError):
            boot.inspect(data)

    def test_reject_wrappers(self):
        with self.assertRaises(ValueError):
            boot.inspect(b"wrapper" + fixture(0))

    def test_recovery_offset(self):
        data = fixture(1)
        struct.pack_into("<Q", data, 1636, 2048)
        with self.assertRaises(ValueError):
            boot.inspect(data)

    def test_unknown_version(self):
        data = fixture(0)
        struct.pack_into("<I", data, 40, 5)
        with self.assertRaises(ValueError):
            boot.inspect(data)

    def test_declared_header_size(self):
        data = fixture(4)
        struct.pack_into("<I", data, 20, 9000)
        with self.assertRaises(ValueError):
            boot.inspect(data)


if __name__ == "__main__":
    unittest.main()

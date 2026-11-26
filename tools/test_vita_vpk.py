import struct
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_vita_vpk import SFO_ENTRY, SFO_HEADER, SFO_MAGIC, SFO_VERSION, VpkError, verify_vpk


def make_sfo(values):
    keys = bytearray()
    data = bytearray()
    entries = []
    for key, value in values.items():
        key_offset = len(keys)
        keys.extend(key.encode("ascii") + b"\0")
        if isinstance(value, int):
            fmt = 0x0404
            raw = struct.pack("<I", value)
        else:
            fmt = 0x0204
            raw = value.encode("utf-8") + b"\0"
        data_offset = len(data)
        data.extend(raw)
        entries.append((key_offset, fmt, len(raw), len(raw), data_offset))
    key_table = SFO_HEADER.size + len(entries) * SFO_ENTRY.size
    data_table = key_table + len(keys)
    header = SFO_HEADER.pack(SFO_MAGIC, SFO_VERSION, key_table, data_table, len(entries))
    index = b"".join(SFO_ENTRY.pack(*entry) for entry in entries)
    return header + index + bytes(keys) + bytes(data)


def make_vpk(path, title_id="VPHB00001", extra=None):
    values = {
        "TITLE": "VitaPluginHub",
        "TITLE_ID": title_id,
        "APP_VER": "00.21",
        "VERSION": "00.00",
        "ATTRIBUTE": 0x00008000,
    }
    files = {
        "sce_sys/param.sfo": make_sfo(values),
        "sce_sys/icon0.png": b"\x89PNG\r\n\x1a\n" + b"\0" * 24,
        "eboot.bin": b"SELF" + b"\0" * 96,
        "plugins.json": b'{"plugins":[]}',
        "cacert.pem": b"-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n",
    }
    if extra:
        files.update(extra)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)


class VitaVpkVerificationTests(unittest.TestCase):
    def test_accepts_expected_vpk_identity_and_numeric_sfo_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path)
            result = verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")
            self.assertEqual(result["title_id"], "VPHB00001")
            self.assertEqual(result["app_version"], "00.21")
            self.assertEqual(result["entries"], 5)

    def test_rejects_wrong_title_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path, title_id="OTHER0001")
            with self.assertRaisesRegex(VpkError, "TITLE_ID mismatch"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_wrong_app_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path)
            with self.assertRaisesRegex(VpkError, "APP_VER mismatch"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.20")

    def test_rejects_missing_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path, extra={"cacert.pem": b"no certificate"})
            with self.assertRaisesRegex(VpkError, "cacert.pem"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path, extra={"../outside": b"bad"})
            with self.assertRaisesRegex(VpkError, "contents mismatch|unsafe VPK path"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_duplicate_archive_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            make_vpk(path)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("plugins.json", b'{"plugins":["unexpected"]}')
            with self.assertRaisesRegex(VpkError, "duplicate VPK paths"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_total_expanded_payload_over_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.vpk"
            make_vpk(path, extra={
                "eboot.bin": b"E" * (24 * 1024 * 1024),
                "sce_sys/icon0.png": b"\\x89PNG\\r\\n\\x1a\\n" + b"I" * (24 * 1024 * 1024),
                "cacert.pem": b"-----BEGIN CERTIFICATE-----\\n" + b"C" * (24 * 1024 * 1024),
            })
            with self.assertRaisesRegex(VpkError, "expanded contents"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_single_entry_over_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized-entry.vpk"
            make_vpk(path, extra={"eboot.bin": b"E" * (32 * 1024 * 1024 + 1)})
            with self.assertRaisesRegex(VpkError, "large VPK entry"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")

    def test_rejects_symbolic_link_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.vpk"
            values = {
                "TITLE": "VitaPluginHub", "TITLE_ID": "VPHB00001",
                "APP_VER": "00.21", "VERSION": "00.00", "ATTRIBUTE": 0x00008000,
            }
            files = {
                "sce_sys/param.sfo": make_sfo(values),
                "sce_sys/icon0.png": b"\\x89PNG\\r\\n\\x1a\\n" + b"\\0" * 24,
                "eboot.bin": b"SELF" + b"\\0" * 96,
                "plugins.json": b'{"plugins":[]}',
                "cacert.pem": b"-----BEGIN CERTIFICATE-----\\nAAAA\\n-----END CERTIFICATE-----\\n",
            }
            with zipfile.ZipFile(path, "w") as archive:
                for name, payload in files.items():
                    info = zipfile.ZipInfo(name)
                    if name == "eboot.bin":
                        info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(info, payload)
            with self.assertRaisesRegex(VpkError, "symbolic links are not allowed"):
                verify_vpk(str(path), "VPHB00001", "VitaPluginHub", "00.21")


if __name__ == "__main__":
    unittest.main()

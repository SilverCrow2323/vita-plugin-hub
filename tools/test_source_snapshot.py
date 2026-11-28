import base64
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.verify_source_snapshot import inspect_tar_archive, verify_snapshot


def make_tar(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name, kind, value in entries:
            info = tarfile.TarInfo(name)
            if kind == "file":
                data = value
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            elif kind == "dir":
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = value
                archive.addfile(info)
            elif kind == "hardlink":
                info.type = tarfile.LNKTYPE
                info.linkname = value
                archive.addfile(info)
    return stream.getvalue()


def write_snapshot(root: Path, archive_bytes: bytes):
    payload = root / ".payload"
    payload.mkdir()
    encoded = base64.b64encode(archive_bytes).decode("ascii")
    chunk_size = (len(encoded) + 5) // 6
    chunks = [encoded[index * chunk_size:(index + 1) * chunk_size] for index in range(6)]
    for index, chunk in enumerate(chunks):
        (payload / f"vph-source-{index:02d}.b64").write_text(chunk, encoding="ascii")
    manifest = root / "SOURCE-MANIFEST.md"
    manifest.write_text(
        "- Base64 SHA-256: " + hashlib.sha256(encoded.encode("ascii")).hexdigest() + "\n"
        "- Decoded tar.gz SHA-256: " + hashlib.sha256(archive_bytes).hexdigest() + "\n",
        encoding="utf-8",
    )
    return payload, manifest


class SourceSnapshotTests(unittest.TestCase):
    def test_accepts_intact_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = make_tar([(".", "dir", b""), ("src/main.c", "file", b"int main(void) { return 0; }\n")])
            payload, manifest = write_snapshot(root, archive)
            self.assertEqual(verify_snapshot(payload, manifest), [])

    def test_rejects_modified_base64_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = make_tar([("src/main.c", "file", b"ok")])
            payload, manifest = write_snapshot(root, archive)
            part = payload / "vph-source-00.b64"
            part.write_text(part.read_text(encoding="ascii") + "A", encoding="ascii")
            errors = verify_snapshot(payload, manifest)
            self.assertTrue(any("Base64 source-part SHA-256" in item for item in errors))

    def test_rejects_path_traversal(self):
        archive = make_tar([("../outside.txt", "file", b"no")])
        self.assertTrue(any("unsafe source archive path" in item for item in inspect_tar_archive(archive)))

    def test_rejects_symlinks_and_hardlinks(self):
        archive = make_tar([
            ("src/link", "symlink", "../../outside"),
            ("src/hardlink", "hardlink", "src/main.c"),
            ("src/main.c", "file", b"ok"),
        ])
        errors = inspect_tar_archive(archive)
        self.assertGreaterEqual(sum("links are not allowed" in item for item in errors), 2)

    def test_rejects_duplicate_members(self):
        archive = make_tar([
            ("src/main.c", "file", b"first"),
            ("src/main.c", "file", b"second"),
        ])
        self.assertTrue(any("duplicate source archive member" in item for item in inspect_tar_archive(archive)))


if __name__ == "__main__":
    unittest.main(verbosity=2)

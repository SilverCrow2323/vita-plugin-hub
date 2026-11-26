import base64
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reconstruct_source import ReconstructionError, reconstruct

def make_archive(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name, payload, kind in entries:
            info = tarfile.TarInfo(name)
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "src/main.c"
                archive.addfile(info)
            elif kind == "hardlink":
                info.type = tarfile.LNKTYPE
                info.linkname = "src/main.c"
                archive.addfile(info)
            else:
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
    return stream.getvalue()

def write_parts(root, archive):
    encoded = base64.b64encode(archive)
    split = max(1, len(encoded) // 2)
    (root / "vph-source-00.b64").write_bytes(encoded[:split])
    (root / "vph-source-01.b64").write_bytes(encoded[split:])

class SafeReconstructionTests(unittest.TestCase):
    def run_fixture(self, entries, expect_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); payload = root / "payload"; output = root / "source"
            payload.mkdir()
            write_parts(payload, make_archive(entries))
            if expect_error:
                with self.assertRaisesRegex(ReconstructionError, expect_error):
                    reconstruct(payload, output)
            else:
                return reconstruct(payload, output), output

    def test_extracts_regular_source_tree(self):
        paths, output = self.run_fixture([
            ("./CMakeLists.txt", b"project(VitaPluginHub)", "file"),
            ("src/", b"", "dir"),
            ("src/main.c", b"int main(void){return 0;}", "file"),
        ])
        self.assertIn("CMakeLists.txt", paths)
        self.assertEqual((output / "src/main.c").read_bytes(), b"int main(void){return 0;}")

    def test_rejects_parent_traversal(self):
        self.run_fixture([
            ("CMakeLists.txt", b"cmake", "file"),
            ("src/main.c", b"code", "file"),
            ("../escape.txt", b"bad", "file"),
        ], "Unsafe archive path")

    def test_rejects_absolute_path(self):
        self.run_fixture([
            ("CMakeLists.txt", b"cmake", "file"),
            ("src/main.c", b"code", "file"),
            ("/tmp/escape", b"bad", "file"),
        ], "Unsafe archive path")

    def test_rejects_symlink_and_hardlink(self):
        for kind in ("symlink", "hardlink"):
            self.run_fixture([
                ("CMakeLists.txt", b"cmake", "file"),
                ("src/main.c", b"code", "file"),
                ("src/link", b"", kind),
            ], "Links and special files")

    def test_rejects_duplicate_paths(self):
        self.run_fixture([
            ("CMakeLists.txt", b"cmake", "file"),
            ("src/main.c", b"first", "file"),
            ("src/main.c", b"second", "file"),
        ], "Duplicate archive path")

    def test_refuses_nonempty_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); payload = root / "payload"; output = root / "source"
            payload.mkdir(); output.mkdir(); (output / "keep.txt").write_text("keep")
            write_parts(payload, make_archive([
                ("CMakeLists.txt", b"cmake", "file"), ("src/main.c", b"code", "file")
            ]))
            with self.assertRaisesRegex(ReconstructionError, "must be empty"):
                reconstruct(payload, output)
            self.assertEqual((output / "keep.txt").read_text(), "keep")

if __name__ == "__main__":
    unittest.main()

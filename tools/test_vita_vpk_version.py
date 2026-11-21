import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from set_vita_vpk_version import VersionPatchError, normalize_vpk_version


class VitaVpkVersionTests(unittest.TestCase):
    def test_changes_only_the_vita_package_version(self):
        source = """
project(VitaPluginHub VERSION 0.2.1 LANGUAGES C CXX)
set(VITA_VERSION 0.2.1)
vita_create_vpk(VitaPluginHub.vpk VPHB00001
    VitaPluginHub.self
    VERSION ${VITA_VERSION}
    NAME VitaPluginHub
)
"""
        result = normalize_vpk_version(source, "00.21")
        self.assertIn("project(VitaPluginHub VERSION 0.2.1", result)
        self.assertIn("set(VITA_VERSION 0.2.1)", result)
        self.assertIn("VERSION 00.21", result)

    def test_rejects_semver_for_package_version(self):
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version("vita_create_vpk(x y z VERSION 0.2.1)", "0.2.1")

    def test_rejects_missing_vpk_declaration(self):
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version("project(VitaPluginHub VERSION 0.2.1)", "00.21")

    def test_rejects_multiple_vpk_declarations(self):
        source = "vita_create_vpk(a b c VERSION 00.01)\nvita_create_vpk(d e f VERSION 00.02)"
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version(source, "00.21")


if __name__ == "__main__":
    unittest.main()

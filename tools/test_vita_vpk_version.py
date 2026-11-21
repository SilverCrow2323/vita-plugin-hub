import unittest

from tools.set_vita_vpk_version import (
    VersionPatchError,
    add_target_link_dependencies,
    normalize_vpk_version,
)


FIXTURE = """
project(VitaPluginHub VERSION 0.2.1 LANGUAGES C CXX)
add_executable(VitaPluginHub src/main.c)
target_link_libraries(VitaPluginHub PRIVATE vita2d curl crypto)
vita_create_vpk(VitaPluginHub.vpk VPHB00001
    VitaPluginHub.self
    VERSION ${VITA_VERSION}
    NAME VitaPluginHub
)
"""


class VitaVpkVersionTests(unittest.TestCase):
    def test_changes_only_the_vita_package_version(self):
        result = normalize_vpk_version(FIXTURE, "00.21")
        self.assertIn("project(VitaPluginHub VERSION 0.2.1", result)
        self.assertIn("VERSION 00.21", result)

    def test_rejects_semver_for_package_version(self):
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version(FIXTURE, "0.2.1")

    def test_rejects_missing_vpk_declaration(self):
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version("project(VitaPluginHub VERSION 0.2.1)", "00.21")

    def test_rejects_multiple_vpk_declarations(self):
        source = FIXTURE + "\nvita_create_vpk(another.vpk OTHER00001 another.self VERSION 00.02)"
        with self.assertRaises(VersionPatchError):
            normalize_vpk_version(source, "00.21")

    def test_adds_only_missing_static_dependencies_with_keyword_signature(self):
        result = add_target_link_dependencies(
            FIXTURE, "VitaPluginHub", ["curl", "pthread", "zstd"], signature="keyword"
        )
        link_lines = "\n".join(
            line for line in result.splitlines()
            if line.strip().startswith("target_link_libraries")
        )
        self.assertIn("target_link_libraries(VitaPluginHub PRIVATE pthread zstd)", link_lines)
        self.assertEqual(link_lines.count("curl"), 1)

    def test_adds_dependencies_to_plain_signature_without_keywords(self):
        plain_fixture = FIXTURE.replace(
            "target_link_libraries(VitaPluginHub PRIVATE",
            "target_link_libraries(VitaPluginHub",
        )
        result = add_target_link_dependencies(
            plain_fixture, "VitaPluginHub", ["curl", "pthread", "zstd"], signature="plain"
        )
        link_lines = "\n".join(
            line for line in result.splitlines()
            if line.strip().startswith("target_link_libraries")
        )
        self.assertIn("target_link_libraries(VitaPluginHub pthread zstd)", link_lines)
        self.assertEqual(link_lines.count("curl"), 1)

    def test_rejects_unknown_signature(self):
        with self.assertRaises(VersionPatchError):
            add_target_link_dependencies(FIXTURE, "VitaPluginHub", ["zstd"], signature="auto")

    def test_rejects_missing_target_name(self):
        with self.assertRaises(VersionPatchError):
            add_target_link_dependencies(FIXTURE, "bad target", ["zstd"])


if __name__ == "__main__":
    unittest.main()

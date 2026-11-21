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

    def test_adds_missing_static_dependency_closure(self):
        result = add_target_link_dependencies(FIXTURE, "VitaPluginHub", ["zstd", "pthread"], signature="keyword")
        self.assertIn("target_link_libraries(VitaPluginHub PRIVATE zstd pthread)", result)

    def test_adds_dependencies_to_plain_signature_without_keywords(self):
        plain_fixture = FIXTURE.replace(
            "target_link_libraries(VitaPluginHub PRIVATE",
            "target_link_libraries(VitaPluginHub",
        )
        result = add_target_link_dependencies(plain_fixture, "VitaPluginHub", ["zstd", "pthread"], signature="plain")
        self.assertIn("target_link_libraries(VitaPluginHub zstd pthread)", result)

    def test_does_not_duplicate_existing_library(self):
        result = add_target_link_dependencies(FIXTURE, "VitaPluginHub", ["curl", "pthread"])
        link_lines = "\\n".join(
            line for line in result.splitlines()
            if line.strip().startswith("target_link_libraries")
        )
        self.assertEqual(link_lines.count("pthread"), 1)
        self.assertEqual(link_lines.count("curl"), 1)
        self.assertFalse(any("PRIVATE curl" in line or line.endswith(" curl)") for line in link_lines.splitlines()))

    def test_rejects_unknown_signature(self):
        with self.assertRaises(VersionPatchError):
            add_target_link_dependencies(FIXTURE, "VitaPluginHub", ["zstd"], signature="auto")

    def test_emits_explicit_target_link_for_cmake_to_resolve(self):
        result = add_target_link_dependencies(FIXTURE, "OtherTarget", ["zstd"], signature="keyword")
        self.assertIn("target_link_libraries(OtherTarget PRIVATE zstd)", result)


if __name__ == "__main__":
    unittest.main()

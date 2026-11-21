#!/usr/bin/env python3
"""Normalize VitaSDK VPK metadata and close required static-library dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VPK_VERSION = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
VPK_CALL = re.compile(
    r"(vita_create_vpk\s*\(.*?\bVERSION\s+)([^\s)]+)",
    re.IGNORECASE | re.DOTALL,
)


class VersionPatchError(ValueError):
    """The CMake VPK declaration cannot be safely normalized."""


def normalize_vpk_version(source: str, version: str) -> str:
    if not VPK_VERSION.fullmatch(version):
        raise VersionPatchError("Vita package version must use the ##.## format")
    if source.lower().count("vita_create_vpk") != 1:
        raise VersionPatchError("expected exactly one vita_create_vpk declaration")
    result, count = VPK_CALL.subn(lambda match: match.group(1) + version, source, count=1)
    if count != 1:
        raise VersionPatchError("vita_create_vpk declaration has no VERSION argument")
    return result


def add_target_link_dependencies(source: str, target: str, libraries: list[str]) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_+-]+", target):
        raise VersionPatchError("invalid CMake target name")

    # The source bundle may declare the executable via a CMake variable
    # (for example add_executable(${APP_TARGET} ...). Do not try to parse
    # arbitrary CMake expressions here; CMake itself validates target names.
    link_blocks = re.findall(
        r"\btarget_link_libraries\s*\(\s*" + re.escape(target) + r"\b(.*?)\)",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    existing: set[str] = set()
    for block in link_blocks:
        existing.update(re.findall(r"[A-Za-z0-9_+-]+", block))

    missing: list[str] = []
    for library in libraries:
        if not re.fullmatch(r"[A-Za-z0-9_+-]+", library):
            raise VersionPatchError("invalid linker library name: %s" % library)
        if library not in existing and library not in missing:
            missing.append(library)

    if missing:
        source = source.rstrip() + "\n\n# VitaSDK static dependency closure for curl/OpenSSL.\n"
        source += "target_link_libraries(%s PRIVATE %s)\n" % (target, " ".join(missing))
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cmake_file", nargs="?", default="CMakeLists.txt")
    parser.add_argument("--version", required=True, help="VitaSDK package version in ##.## format")
    parser.add_argument("--target", default=None, help="CMake executable target receiving extra static libraries")
    parser.add_argument("--link-library", action="append", default=[], help="Additional target library (repeatable)")
    args = parser.parse_args()
    path = Path(args.cmake_file)

    try:
        original = path.read_text(encoding="utf-8")
        updated = normalize_vpk_version(original, args.version)
        if args.link_library:
            if not args.target:
                raise VersionPatchError("--target is required when --link-library is used")
            updated = add_target_link_dependencies(updated, args.target, args.link_library)
        path.write_text(updated, encoding="utf-8")
    except (OSError, UnicodeError, VersionPatchError) as exc:
        print("Vita CMake normalization: ERROR: %s" % exc, file=sys.stderr)
        return 1

    print(
        "Vita CMake normalization: VPK version %s; additional static libraries: %s"
        % (args.version, ", ".join(args.link_library) or "none")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

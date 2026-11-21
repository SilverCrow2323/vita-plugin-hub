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


def add_target_link_dependencies(
    source: str,
    target: str,
    libraries: list[str],
    signature: str = "plain",
) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_+-]+", target):
        raise VersionPatchError("invalid CMake target name")
    if signature not in {"plain", "keyword"}:
        raise VersionPatchError("CMake link signature must be plain or keyword")

    # This Vita app has one executable target. Its CMake declaration may use
    # a variable as the target name, so collect the link items from all
    # target_link_libraries blocks instead of guessing how that variable expands.
    existing: set[str] = set()
    blocks = re.findall(
        r"\btarget_link_libraries\s*\((.*?)\)",
        source,
        flags=re.IGNORECASE | re.DOTALL,
    )
    structural = {"PRIVATE", "PUBLIC", "INTERFACE", "DEBUG", "OPTIMIZED", "GENERAL"}
    for block in blocks:
        tokens = re.findall(r"[A-Za-z0-9_+-]+", block)
        for token in tokens[1:]:
            if token.upper() not in structural:
                existing.add(token)

    missing: list[str] = []
    for library in libraries:
        if not re.fullmatch(r"[A-Za-z0-9_+-]+", library):
            raise VersionPatchError("invalid linker library name: %s" % library)
        if library not in existing and library not in missing:
            missing.append(library)

    if missing:
        source = source.rstrip() + "\n\n# VitaSDK static dependency closure for curl/OpenSSL.\n"
        scope = "PRIVATE " if signature == "keyword" else ""
        source += "target_link_libraries(%s %s%s)\n" % (target, scope, " ".join(missing))
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cmake_file", nargs="?", default="CMakeLists.txt")
    parser.add_argument("--version", required=True, help="VitaSDK package version in ##.## format")
    parser.add_argument("--target", default=None, help="CMake executable target receiving extra static libraries")
    parser.add_argument("--link-library", action="append", default=[], help="Additional target library (repeatable)")
    parser.add_argument("--signature", choices=("plain", "keyword"), default="plain",
                        help="CMake target_link_libraries signature used by the source project")
    args = parser.parse_args()
    path = Path(args.cmake_file)

    try:
        original = path.read_text(encoding="utf-8")
        updated = normalize_vpk_version(original, args.version)
        if args.link_library:
            if not args.target:
                raise VersionPatchError("--target is required when --link-library is used")
            updated = add_target_link_dependencies(updated, args.target, args.link_library, args.signature)
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

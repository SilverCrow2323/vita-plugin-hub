#!/usr/bin/env python3
"""Normalize only the VitaSDK VPK VERSION argument, preserving semantic project versions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VPK_VERSION = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
CALL = re.compile(r"(vita_create_vpk\s*\(.*?\bVERSION\s+)([^\s)]+)", re.IGNORECASE | re.DOTALL)


class VersionPatchError(ValueError):
    """The CMake VPK declaration cannot be safely normalized."""


def normalize_vpk_version(source: str, version: str) -> str:
    if not VPK_VERSION.fullmatch(version):
        raise VersionPatchError("Vita package version must use the ##.## format")
    call_count = len(re.findall(r"\\bvita_create_vpk\\s*\\(", source, flags=re.IGNORECASE))
    if call_count != 1:
        raise VersionPatchError("expected exactly one vita_create_vpk declaration")
    result, count = CALL.subn(lambda match: match.group(1) + version, source, count=1)
    if count != 1:
        raise VersionPatchError("vita_create_vpk declaration has no VERSION argument")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cmake_file", nargs="?", default="CMakeLists.txt")
    parser.add_argument("--version", required=True, help="VitaSDK package version in ##.## format")
    args = parser.parse_args()
    path = Path(args.cmake_file)
    try:
        original = path.read_text(encoding="utf-8")
        updated = normalize_vpk_version(original, args.version)
        path.write_text(updated, encoding="utf-8")
    except (OSError, UnicodeError, VersionPatchError) as exc:
        print("Vita VPK version normalization: ERROR: %s" % exc, file=sys.stderr)
        return 1
    print("Vita VPK package version normalized to %s; semantic project version left untouched." % args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

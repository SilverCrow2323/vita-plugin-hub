#!/usr/bin/env python3
"""Verify VitaPluginHub VPK structure, safe paths and PARAM.SFO identity."""

from __future__ import annotations

import argparse
import json
import os
import stat
import struct
import sys
import zipfile
from pathlib import PurePosixPath
from typing import Dict

SFO_HEADER = struct.Struct("<4sIIII")
SFO_ENTRY = struct.Struct("<HHIII")
SFO_MAGIC = b"\x00PSF"
SFO_VERSION = 0x00000101
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
REQUIRED_FILES = {
    "sce_sys/param.sfo",
    "sce_sys/icon0.png",
    "eboot.bin",
    "plugins.json",
    "cacert.pem",
}


class VpkError(ValueError):
    """The VPK is malformed or its package identity is not as expected."""


def parse_sfo(data: bytes) -> Dict[str, str]:
    if len(data) < SFO_HEADER.size:
        raise VpkError("PARAM.SFO is shorter than its header")
    magic, version, key_table, data_table, count = SFO_HEADER.unpack_from(data)
    if magic != SFO_MAGIC or version != SFO_VERSION:
        raise VpkError("PARAM.SFO magic or version is invalid")
    entries_end = SFO_HEADER.size + count * SFO_ENTRY.size
    if entries_end > len(data) or key_table < entries_end or data_table < key_table or data_table > len(data):
        raise VpkError("PARAM.SFO table offsets are outside the file")

    values: Dict[str, str] = {}
    for index in range(count):
        offset = SFO_HEADER.size + index * SFO_ENTRY.size
        key_offset, fmt, length, max_length, value_offset = SFO_ENTRY.unpack_from(data, offset)
        key_start = key_table + key_offset
        if key_start >= data_table:
            raise VpkError("PARAM.SFO key offset is outside the key table")
        key_end = data.find(b"\0", key_start, data_table)
        if key_end < 0:
            raise VpkError("PARAM.SFO key is not NUL terminated")
        try:
            key = data[key_start:key_end].decode("ascii")
        except UnicodeDecodeError as exc:
            raise VpkError("PARAM.SFO key is not ASCII") from exc
        value_start = data_table + value_offset
        if length > max_length or value_start + length > len(data):
            raise VpkError("PARAM.SFO value is outside the data table")
        raw = data[value_start:value_start + length]
        if fmt == 0x0204:
            try:
                value = raw.split(b"\\0", 1)[0].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise VpkError("PARAM.SFO value is not UTF-8 for %s" % key) from exc
        elif fmt == 0x0404 and length == 4:
            value = struct.unpack("<I", raw)[0]
        else:
            raise VpkError("unsupported PARAM.SFO value format for %s: 0x%04x" % (key, fmt))
        if key in values:
            raise VpkError("duplicate PARAM.SFO key: %s" % key)
        values[key] = value
    return values


def verify_vpk(path: str, title_id: str, title: str, app_version: str) -> Dict[str, object]:
    try:
        archive = zipfile.ZipFile(path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise VpkError("cannot open VPK: %s" % exc) from exc

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise VpkError("duplicate VPK paths are not allowed")
        if set(names) != REQUIRED_FILES:
            missing = sorted(REQUIRED_FILES - set(names))
            extra = sorted(set(names) - REQUIRED_FILES)
            raise VpkError("VPK contents mismatch (missing=%r extra=%r)" % (missing, extra))

        for info in infos:
            entry_path = PurePosixPath(info.filename)
            if info.filename.startswith("/") or "\\" in info.filename or ".." in entry_path.parts:
                raise VpkError("unsafe VPK path: %s" % info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise VpkError("symbolic links are not allowed: %s" % info.filename)
            if info.file_size > 32 * 1024 * 1024:
                raise VpkError("unexpectedly large VPK entry: %s" % info.filename)

        bad_member = archive.testzip()
        if bad_member is not None:
            raise VpkError("VPK CRC check failed for %s" % bad_member)

        sfo = parse_sfo(archive.read("sce_sys/param.sfo"))
        expected = {
            "TITLE": title,
            "TITLE_ID": title_id,
            "APP_VER": app_version,
        }
        for key, value in expected.items():
            if sfo.get(key) != value:
                raise VpkError("PARAM.SFO %s mismatch: expected %r, got %r" % (key, value, sfo.get(key)))

        icon = archive.read("sce_sys/icon0.png")
        if not icon.startswith(PNG_MAGIC):
            raise VpkError("sce_sys/icon0.png is not a PNG file")
        executable = archive.read("eboot.bin")
        if len(executable) < 64:
            raise VpkError("eboot.bin is unexpectedly small")
        catalog = json.loads(archive.read("plugins.json").decode("utf-8"))
        if not isinstance(catalog, dict):
            raise VpkError("plugins.json root must be an object")
        certificate = archive.read("cacert.pem")
        if b"-----BEGIN CERTIFICATE-----" not in certificate:
            raise VpkError("cacert.pem contains no PEM certificate")

        return {
            "entries": len(infos),
            "vpk_bytes": os.path.getsize(path),
            "eboot_bytes": len(executable),
            "title": sfo["TITLE"],
            "title_id": sfo["TITLE_ID"],
            "app_version": sfo["APP_VER"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vpk")
    parser.add_argument("--title-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--app-version", required=True)
    args = parser.parse_args()
    try:
        result = verify_vpk(args.vpk, args.title_id, args.title, args.app_version)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, VpkError) as exc:
        print("VPK verification: ERROR: %s" % exc, file=sys.stderr)
        return 1
    print(
        "VPK verification: OK (%d entries; %s / %s / APP_VER %s; eboot %d bytes)"
        % (result["entries"], result["title"], result["title_id"], result["app_version"], result["eboot_bytes"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify the VitaPluginHub source snapshot before any archive extraction."""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import re
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PARTS = [f"vph-source-{index:02d}.b64" for index in range(6)]
MAX_COMPRESSED_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 10000


def expected_digest(manifest: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in manifest.splitlines():
        if line.startswith(prefix):
            value = re.sub(r"[^0-9a-f]", "", line.split(":", 1)[1])
            return value if len(value) == 64 else None
    return None


def inspect_tar_archive(payload: bytes) -> list[str]:
    errors: list[str] = []
    if len(payload) > MAX_COMPRESSED_BYTES:
        return ["decoded source archive exceeds the compressed byte budget"]
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError, EOFError) as exc:
        return [f"source archive is not a readable gzip tar: {exc}"]

    if not members:
        return ["source archive is empty"]
    if len(members) > MAX_MEMBERS:
        return ["source archive exceeds the member-count budget"]

    seen: set[str] = set()
    expanded = 0
    regular_files = 0
    for member in members:
        name = member.name
        path = PurePosixPath(name)
        normalized = path.as_posix()
        if (
            not name
            or "\\" in name
            or path.is_absolute()
            or ".." in path.parts
            or re.match(r"^[A-Za-z]:", name)
        ):
            errors.append(f"unsafe source archive path: {name!r}")
            continue
        if normalized in ("", "."):
            errors.append("source archive contains an empty/root member")
            continue
        if normalized in seen:
            errors.append(f"duplicate source archive member: {normalized}")
        seen.add(normalized)

        if member.issym() or member.islnk():
            errors.append(f"source archive links are not allowed: {normalized}")
        elif member.isfile():
            regular_files += 1
            if member.size < 0:
                errors.append(f"negative source archive member size: {normalized}")
            else:
                expanded += member.size
        elif not member.isdir():
            errors.append(f"unsupported source archive member type: {normalized}")

    if expanded > MAX_EXPANDED_BYTES:
        errors.append("source archive exceeds the expanded byte budget")
    if regular_files == 0:
        errors.append("source archive contains no regular files")
    return errors


def verify_snapshot(payload_dir: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read source manifest: {exc}"]

    expected_base64 = expected_digest(manifest, "Base64 SHA-256")
    expected_archive = expected_digest(manifest, "Decoded tar.gz SHA-256")
    if not expected_base64 or not expected_archive:
        return ["source manifest is missing a valid SHA-256 declaration"]

    parts = sorted(payload_dir.glob("vph-source-*.b64"))
    names = [part.name for part in parts]
    if names != EXPECTED_PARTS:
        return [f"expected ordered payload parts {EXPECTED_PARTS}, found {names}"]

    try:
        encoded = "".join(
            re.sub(r"\s+", "", part.read_text(encoding="ascii")) for part in parts
        )
    except (OSError, UnicodeError) as exc:
        return [f"cannot read Base64 source parts: {exc}"]

    actual_base64 = hashlib.sha256(encoded.encode("ascii")).hexdigest()
    if actual_base64 != expected_base64:
        errors.append("Base64 source-part SHA-256 does not match SOURCE-MANIFEST.md")

    try:
        archive_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        return errors + [f"source parts are not valid Base64: {exc}"]

    actual_archive = hashlib.sha256(archive_bytes).hexdigest()
    if actual_archive != expected_archive:
        errors.append("decoded source archive SHA-256 does not match SOURCE-MANIFEST.md")
    errors.extend(inspect_tar_archive(archive_bytes))
    return errors


def main() -> int:
    errors = verify_snapshot(ROOT / ".payload", ROOT / "SOURCE-MANIFEST.md")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("VitaPluginHub source snapshot: digests and archive paths verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

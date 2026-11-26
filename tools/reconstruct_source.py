#!/usr/bin/env python3
"""Safely reconstruct the VitaPluginHub source snapshot from ordered Base64 parts."""
from __future__ import annotations
import argparse, base64, binascii, io, re, sys, tarfile
from pathlib import Path, PurePosixPath

MAX_ENCODED = 8 * 1024 * 1024
MAX_ARCHIVE = 6 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
MAX_MEMBERS = 4096
MAX_PATH_BYTES = 240
MAX_DEPTH = 16
PART_RE = re.compile(r"^vph-source-(\d{2})\.b64$")

class ReconstructionError(ValueError):
    pass

def read_parts(payload_dir: Path) -> bytes:
    parts = sorted(payload_dir.glob("vph-source-*.b64"))
    if not parts:
        raise ReconstructionError("No vph-source-*.b64 parts found")
    if sum(path.stat().st_size for path in parts) > MAX_ENCODED:
        raise ReconstructionError("Encoded source payload exceeds size limit")
    numbers = []
    chunks = []
    for path in parts:
        match = PART_RE.fullmatch(path.name)
        if not match:
            raise ReconstructionError(f"Unexpected payload part name: {path.name}")
        numbers.append(int(match.group(1)))
        chunks.append(re.sub(rb"\s+", b"", path.read_bytes()))
    if numbers != list(range(len(numbers))):
        raise ReconstructionError("Payload parts must be contiguous and start at 00")
    try:
        archive = base64.b64decode(b"".join(chunks), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ReconstructionError(f"Invalid Base64 source payload: {exc}") from exc
    if not archive or len(archive) > MAX_ARCHIVE:
        raise ReconstructionError("Decoded source archive is empty or exceeds size limit")
    return archive

def normalized_member_name(name: str) -> str:
    if not name or "\\" in name or name.startswith("/"):
        raise ReconstructionError(f"Unsafe archive path: {name!r}")
    while name.startswith("./"):
        name = name[2:]
    name = name.rstrip("/")
    if not name:
        return ""
    raw_parts = name.split("/")
    if len(name.encode("utf-8")) > MAX_PATH_BYTES or len(raw_parts) > MAX_DEPTH:
        raise ReconstructionError(f"Archive path exceeds limits: {name!r}")
    if any(part in ("", ".", "..") or ":" in part for part in raw_parts):
        raise ReconstructionError(f"Unsafe archive path: {name!r}")
    path = PurePosixPath(*raw_parts)
    if path.is_absolute():
        raise ReconstructionError(f"Absolute archive path: {name!r}")
    return path.as_posix()

def reconstruct(payload_dir: Path, output_dir: Path) -> list[str]:
    archive_bytes = read_parts(payload_dir)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ReconstructionError(f"Output directory must be empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []
    seen: set[str] = set()
    total_size = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > MAX_MEMBERS:
                raise ReconstructionError("Source archive contains too many entries")
            for member in members:
                name = normalized_member_name(member.name)
                if not name:
                    if member.isdir():
                        continue
                    raise ReconstructionError("Archive contains an empty file path")
                if name in seen:
                    raise ReconstructionError(f"Duplicate archive path: {name}")
                seen.add(name)
                target = output_dir.joinpath(*PurePosixPath(name).parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile() or member.issym() or member.islnk():
                    raise ReconstructionError(f"Links and special files are not allowed: {name}")
                total_size += member.size
                if member.size < 0 or total_size > MAX_EXPANDED:
                    raise ReconstructionError("Expanded source archive exceeds size limit")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ReconstructionError(f"Cannot read archive member: {name}")
                written = 0
                with source, target.open("xb") as destination:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > member.size:
                            raise ReconstructionError(f"Archive member exceeded declared size: {name}")
                        destination.write(chunk)
                if written != member.size:
                    raise ReconstructionError(f"Archive member size mismatch: {name}")
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
                extracted.append(name)
        if "CMakeLists.txt" not in extracted or not any(name.startswith("src/") for name in extracted):
            raise ReconstructionError("Source snapshot is missing root CMakeLists.txt or src/")
    except (tarfile.TarError, OSError) as exc:
        raise ReconstructionError(f"Cannot reconstruct source archive: {exc}") from exc
    return extracted

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-dir", type=Path, default=Path(".payload"))
    parser.add_argument("--output", type=Path, default=Path(".vph-source"))
    args = parser.parse_args()
    try:
        paths = reconstruct(args.payload_dir, args.output)
    except (OSError, ReconstructionError) as exc:
        print(f"reconstruct-source: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Reconstructed {len(paths)} regular files into {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

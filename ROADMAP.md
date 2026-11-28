# VitaPluginHub — Roadmap

## Phase 1 — Reproducible source and build
- Verify the ordered .payload parts against the Base64 SHA-256 in SOURCE-MANIFEST.md.
- Verify the decoded archive SHA-256 before extraction.
- Reject archive traversal, duplicate members, symlinks, hardlinks and special files before extraction.
- Restore source, run host tests, build the VPK with the pinned VitaSDK and verify PARAM.SFO, required files and checksums.

Acceptance: an altered part, wrong digest or unsafe tar member fails before extraction; an intact snapshot produces the verified source tree and a valid VPK artifact.

## Phase 2 — Catalogue correctness and provenance
- Validate every catalogue record against the schema.
- Preserve upstream repository, release and compatibility references.
- Distinguish upstream-authored digests from locally computed hashes.
- Mark uncertain, stale or unverified compatibility information explicitly.

Acceptance: malformed entries fail CI; each displayed plugin has a traceable upstream source; no local digest is presented as publisher authentication.

## Phase 3 — Read-only configuration workflows
- Inspect taiHEN and Adrenaline plugin lists without changing them.
- Back up supported configuration files with timestamps and integrity metadata.
- Report missing files, parse errors and unsupported layouts without attempting repair.

Acceptance: malformed input never causes a write; backup/restore is tested against fixtures; secrets and identifiers are redacted.

## Phase 4 — Controlled installation planning
- Define a versioned mapping contract for plugin destinations, dependencies, conflicts and supported firmware.
- Require explicit review and confirmation for every planned mutation.
- Add transactional staging, backup and rollback only after Vita-specific APIs and recovery paths are verified.

Acceptance: no plugin can be installed from advisory metadata alone; interrupted operations leave the prior configuration recoverable.

## Phase 5 — Physical qualification and release
- Test cold start, controller navigation, network failures, downloads, VPK verification and backup inspection on Vita 1000 and a second supported device.
- Record firmware, taiHEN, storage and plugin versions in the test report.
- Publish only after a maintainer reviews the artifact, source attribution and release notes.

Acceptance: a signed-off hardware matrix, reproducible VPK checksum and release notes that separate tested combinations from untested ones.

## Current blockers
- No automatic plugin installation or configuration mutation is implemented.
- Physical Vita qualification is still required.
- Upstream compatibility and publisher identity cannot be inferred from a GitHub release URL or a SHA-256 checksum alone.

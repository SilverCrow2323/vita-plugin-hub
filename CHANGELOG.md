# Changelog

## 0.2.1-rc.1

This is a source release candidate. A stable VPK release is gated on a successful VitaSDK build and real-console verification.

- Curated offline catalog: 16 entries across 9 categories.
- Separated Vita taiHEN and Adrenaline / PSP plugin platforms.
- Added latest-release lookup and guarded downloads from known upstream GitHub repositories.
- Added download progress, HTTPS certificate verification, origin checks, size limits and SHA-256 verification when an upstream digest is available.
- Added read-only taiHEN config inspection and missing-plugin detection.
- Added read-only Adrenaline plugin-list inspection.
- Added timestamped backups for available taiHEN and Ensō configuration files.
- Added host-side catalog validation and smoke tests.
- Added VitaSDK GitHub Actions build and tag-based release publication.

### Known limitations

- Automatic plugin installation, archive extraction and removal are not enabled.
- taiHEN config and Adrenaline plugin lists are read-only.
- Exact asset mappings, dependencies, conflict metadata and rollback procedures need upstream-by-upstream review before installation can be enabled.
- Not yet tested on a physical PS Vita.

## 0.1.0-dev

- Initial VitaSDK/libvita2d shell, catalog model and safety documentation.

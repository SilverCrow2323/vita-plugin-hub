# VitaPluginHub

**A safety-first native plugin catalog and management companion for PlayStation Vita.**

- Target: PS Vita / PlayStation TV
- Reference device: PS Vita OLED (PCH-1000), firmware 3.65 Ensō, SD2Vita + Sony Memory Card
- Interface language: English
- Application title ID: `VPHB00001`
- Planned release line: `0.2.1`

## Repository status

The dedicated repository has been initialized. The complete source snapshot and local validation results are prepared in the accompanying development workspace, but the application source tree has not yet been committed here.

No VPK release is published. The application still requires a real VitaSDK cross-build and a smoke test on a PS Vita before a release candidate can be declared.

## Product scope

- Offline-first curated catalog of official upstream plugin projects.
- Separate platform handling for Vita taiHEN and Adrenaline/PSP.
- GitHub release lookup and guarded download of official release assets.
- Read-only taiHEN and Adrenaline configuration inspection.
- Timestamped configuration backups.
- Planned safe plugin management with dependency, conflict and rollback handling.

## Safety policy

- Downloads are saved for review and are never installed or executed automatically in the current development build.
- Configuration inspection is read-only.
- Vita taiHEN and Adrenaline/PSP plugin systems are kept separate.
- Compatibility metadata is advisory and must be checked against upstream documentation.

## Build

The source uses VitaSDK, CMake, libvita2d, libcurl and OpenSSL. Build instructions will be added with the committed source tree.

## License

The VitaPluginHub source is licensed under the MIT License. Third-party plugins remain the property of their respective authors and retain their own licenses.

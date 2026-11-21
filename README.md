# VitaPluginHub

**A safety-first native plugin catalog and management companion for PlayStation Vita.**

- Target: PS Vita / PlayStation TV
- Reference device: PS Vita OLED (PCH-1000), firmware 3.65 Ensō, SD2Vita + Sony Memory Card
- Interface language: English
- Application title ID: `VPHB00001`
- Development version: `0.2.1-dev`

## Project status

This repository contains the complete VitaPluginHub source project. The current development build provides an offline catalog, online GitHub release lookup, guarded official-asset downloads, read-only taiHEN and Adrenaline inspection, and timestamped configuration backups.

**It is not yet a stable or console-validated release.** Automatic plugin installation, archive extraction, taiHEN config editing, PSP plugin-list editing and rollback of installed plugin binaries remain disabled until exact install plans and device tests are complete.

## Build

The project uses VitaSDK, CMake, libvita2d, libcurl and OpenSSL. See the source package's `README.md` and `.github/workflows/build.yml` for the reproducible build instructions.

## Safety model

- Vita taiHEN and Adrenaline/PSP plugins are treated as separate platforms.
- Downloads are restricted to official GitHub releases belonging to the repository listed in the catalog.
- Downloads are saved for review; they are never installed or executed automatically.
- Configuration inspection is read-only. Backups are created before any future write operation.
- Compatibility metadata is advisory and must be verified against upstream documentation.

## License

The VitaPluginHub source is licensed under GPL-3.0-or-later. Third-party plugins remain the property of their respective authors and retain their own licenses.

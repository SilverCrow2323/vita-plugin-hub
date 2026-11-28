# VitaPluginHub — Project Definition

## Purpose
VitaPluginHub is a safety-first, offline-capable native companion for discovering PlayStation Vita and PSP plugins, reviewing upstream release assets, and inspecting supported plugin configuration. It is not an automatic plugin installer.

## Users and use cases
- Vita and PlayStation TV owners who need a traceable catalogue of plugin purpose, upstream source, dependencies and compatibility notes.
- Maintainers who review upstream releases and need a bounded, reproducible VPK verification/build process.
- Users who need read-only inspection and timestamped backups of taiHEN/Ensō or Adrenaline configuration before manual changes.

## Scope and boundaries
In scope: offline catalogue browsing; upstream repository and release metadata; guarded downloads for review; TLS/origin checks; SHA-256 verification when an upstream digest is actually published; read-only taiHEN and Adrenaline list inspection; configuration backup; and explicit compatibility notes.

Out of scope: executing downloaded assets, silently installing or enabling plugins, editing taiHEN/Ensō boot configuration, changing YAMT storage settings, modifying Adrenaline plugin lists, or treating advisory dependency/conflict metadata as an installation plan.

## Target and runtime
- Hardware: PlayStation Vita and PlayStation TV.
- Native toolchain: VitaSDK 2026.08.
- Application title ID: VPHB00001.
- Current development snapshot: 0.2.1-rc.1.
- UI/documentation language: English.
- Compatibility is per plugin and upstream release; the reference Vita 1000 / firmware 3.65 Ensō setup is not a blanket compatibility claim.

## Architecture
- Native Vita UI and offline catalogue.
- Release lookup/download adapter with strict HTTPS, hostname and origin validation.
- VPK verifier with compressed-size, expanded-size, duplicate-entry, encryption and path-safety limits.
- Read-only taiHEN and Adrenaline configuration readers plus timestamped backup.
- Source restoration from six ordered Base64 parts under .payload; restored source is not trusted until declared digests and archive member paths pass validation.

## Dependencies and integration
VitaSDK, libvita2d, curl, OpenSSL, zlib and the pinned source snapshot. Third-party plugins remain owned and licensed by their upstream authors. The app links to upstream projects; it does not redistribute plugin payloads.

## Security, accessibility and localization
- Validate TLS certificates and hostnames; reject downgrade, untrusted redirects and unexpected asset origins.
- Bound compressed and expanded VPK size before reading entries; reject encrypted, duplicate, traversal and symlink entries.
- Never execute downloaded files. Keep config inspection read-only and backups explicit.
- Redact credentials and device identifiers from logs and reports.
- Keep controller navigation, focus visibility and readable text at Vita resolution.
- English is the current interface language; translations require maintained string resources and layout checks.

## Verified baseline
The repository contains a versioned source snapshot, catalogue validator, host smoke tests, VPK verifier and VitaSDK build workflow. CI can build and package a VPK artifact. The current app deliberately does not install plugins automatically. No stable release or physical-console qualification is claimed by this project brief.

## Release target
A hardware-qualified alpha must pass source-snapshot integrity checks, catalogue and VPK host tests, VitaSDK build/VPK inspection, then physical Vita installation and read-only workflow checks. A stable release additionally needs documented compatibility provenance and a reviewed license/attribution inventory.

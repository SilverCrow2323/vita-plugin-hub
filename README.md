# VitaPluginHub

**A safety-first native plugin catalog and management companion for PlayStation Vita.**

- Target: PS Vita / PlayStation TV
- Reference device: PS Vita OLED (PCH-1000), firmware 3.65 Ensō, SD2Vita + Sony Memory Card
- Interface language: English
- Application title ID: `VPHB00001`
- Development snapshot: `0.2.1-rc.1`

## Project status

The complete application source snapshot is versioned in this repository under `.payload/` as six Base64 parts. GitHub Actions reconstructs the source tree before validation and VitaSDK compilation.

**No stable release or console-validated VPK is published yet.** The native application still requires a successful VitaSDK build and a smoke test on real hardware. The current development build intentionally does not install or modify plugins automatically.

## Included functionality

- Native PS Vita UI in English.
- Offline-first catalog with categories and separate Vita taiHEN / Adrenaline-PSP platforms.
- Plugin descriptions, upstream repositories, compatibility hints and dependencies.
- GitHub release lookup and guarded official release-asset downloads.
- Download progress, certificate verification, origin checks and SHA-256 verification when upstream publishes a digest.
- Read-only taiHEN configuration inspection and missing-file detection.
- Read-only Adrenaline plugin-list inspection.
- Timestamped backups of available taiHEN and Ensō configuration files.

## Safety limitations

- Downloaded assets are saved for review, never executed or installed automatically.
- taiHEN config and Adrenaline plugin lists are currently read-only.
- Dependency and conflict metadata is advisory; unreviewed install mappings remain locked.
- Compatibility claims must be checked against the upstream project's documentation.
- YAMT, Ensō boot configuration, Vita and PSP plugin systems are treated as separate installation domains.

## Reconstruct the source locally

From the repository root:

```bash
mkdir -p /tmp/vitapluginhub-source
python3 tools/reconstruct_source.py --payload-dir .payload --output /tmp/vitapluginhub-source
cd /tmp/vitapluginhub-source
```

The archive contains the C/VitaSDK source, catalog, tests and technical documentation. The workflow file and repository-level README/changelog remain directly visible in the repository.

## Build with VitaSDK

Install VitaSDK and its packages, then:

```bash
export VITASDK=/usr/local/vitasdk
export PATH="$VITASDK/bin:$PATH"
vdpm install libvita2d curl openssl zlib
curl --fail --location --proto '=https' --tlsv1.2 https://curl.se/ca/cacert.pem -o cacert.pem
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE="$VITASDK/share/vita.toolchain.cmake"
cmake --build build --parallel
```

The expected output is `build/VitaPluginHub.vpk`. The GitHub Actions workflow performs catalog checks, host smoke tests, VitaSDK compilation and release publication for pushed `v*` tags.

## Controls

| Input | Action |
|---|---|
| D-pad Up / Down | Navigate |
| D-pad Left / Right | Change category / release asset |
| Cross | Select / open / download selected asset |
| Circle | Back |
| Triangle | Cycle platform filter |
| Select | Search |
| Square | Context action (clear search / check release / backup) |
| Start | Return Home |

## License

VitaPluginHub source: MIT. Third-party plugins remain the property of their respective authors and retain their own licenses.

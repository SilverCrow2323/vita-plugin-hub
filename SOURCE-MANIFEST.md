# Source Snapshot Manifest

- Project: VitaPluginHub
- Snapshot: 0.2.1-rc.1
- Source archive: gzip-compressed tar, Base64 split into six ordered parts
- Payload directory: `.payload/`
- Parts: `vph-source-00.b64` through `vph-source-05.b64`
- Concatenated Base64 size: 41,760 bytes
- Base64 SHA-256: `72aaaa149526fe0e51863fc44c9128ccf29c1c938b8b9974a63a080e3885edbc`
- Decoded tar.gz SHA-256: `9d0830cae3f5103e6cca95d3175e1648ba79c3a63d3749303f45df92797946cc`

## Restore

```bash
cat .payload/vph-source-*.b64 | base64 --decode > VitaPluginHub-source.tar.gz
sha256sum -c <<'EOF'
9d0830cae3f5103e6cca95d3175e1648ba79c3a63d3749303f45df92797946cc  VitaPluginHub-source.tar.gz
EOF
mkdir -p source
tar -xzf VitaPluginHub-source.tar.gz --no-same-owner -C source
```

The GitHub Actions workflow performs the same reconstruction before validation and VitaSDK compilation.

The source bundle deliberately excludes the root README, CHANGELOG, workflow and CA certificate bundle. The workflow fetches the CA bundle from the official curl distribution endpoint before building; the root documentation remains directly browsable in this repository.

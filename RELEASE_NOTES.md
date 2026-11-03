# 1.0.0-rc10 — Windows prerelease

**English** | **[简体中文更新记录](docs/zh-CN/CHANGELOG.md)**

**NBA 2K27 / Windows 10–11 x64 / quick play only.** Independent utility; other editions/platforms are unsupported.

## Automatic continuation after roster patches

A game or patch changing the roster at the configured save location no longer requires manual re-import. The app validates the current roster, builds and verifies the update, then saves its exact input manifest and roster blob as a complete recovery copy before committing. Original recovery baselines and older backups remain. The result and log identify automatic adoption.

Invalid/incompatible data, another installation binding, backup failure, a running game or changes during synchronization still stop the operation and block game launch. Advanced manual re-import remains available when intentionally replacing the original baseline. The rc9 partial-depth fallback remains included.

## Downloads

- `Roster-Beacon-1.0.0-rc10-windows-x64-setup.exe` — install over the existing utility; settings remain.
- `Roster-Beacon-1.0.0-rc10-windows-x64-portable.zip` — extract the whole package.
- `Roster-Beacon-1.0.0-rc10-source.zip`, `SHA256SUMS.txt`, `release-manifest.json`.

No automated tests are added or run. Runtime integrity checks remain enabled. Installation and update-only execution are recorded separately in release delivery notes; in-game adoption and Steam remain for user verification. No game is launched by this delivery.

Source and original-code MIT license: [c01-in/roster-beacon](https://github.com/c01-in/roster-beacon). Bundled runtime notices remain included. Game files, downloaded datasets, private settings, diagnostics and private history are excluded. Provider/game-modification disclosures and rights-holder contact remain in README/About and the first-use notice. Binaries are unsigned.

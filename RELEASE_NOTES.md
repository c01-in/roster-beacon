# 1.0.0-rc9 — Windows prerelease

**English** | **[简体中文更新记录](docs/zh-CN/CHANGELOG.md)**

**NBA 2K27 / Windows 10–11 x64 / quick play only.** Independent utility. Other game editions/platforms are unsupported; Steam in-game adoption still needs on-device verification.

## Fix

ESPN can return only some depth-chart positions. The observed Denver response contained PF/C but no PG/SG/SF; rc8 stopped before reaching its existing missing-player fallback.

- Default fallback now uses actual local positions and previous lineup order for missing source positions, while updating matched transfers and injuries when safe.
- If no safe five-position lineup can be formed, preserve the whole team and defer related transfers. No fabricated players or starters.
- Same-position duplicates retain their first occurrence; cross-position entries remain valid.
- Bilingual fallback details identify missing positions. Wrong team/season, invalid records, absent whole charts and strict-mode missing positions still stop updates and game launch.
- Exceptional depth responses remain available after failure and clear after successful commit.

## Artifacts

- `Roster-Beacon-1.0.0-rc9-windows-x64-setup.exe`
- `Roster-Beacon-1.0.0-rc9-windows-x64-portable.zip`
- `Roster-Beacon-1.0.0-rc9-source.zip`
- `SHA256SUMS.txt` and `release-manifest.json`

Install over the existing utility to retain settings. Portable users extract the whole package; retain their local settings separately. The utility never supplies proprietary rosters or new player assets.

No automated tests or game launch were performed. Copy-only builds succeeded for the current 30-team feed and a diagnostic replay of the saved partial Denver reply (516/521 matched players). The replay combines two source times and was never installed. The existing modified-manifest guard correctly blocked installation against changed local state; re-import the current roster through Advanced settings when that guard applies. See [validation record](docs/验证记录.md). Native file integrity checks remain enabled. UI interaction and in-game adoption remain for user verification.

## Distribution and notices

Source: [c01-in/roster-beacon](https://github.com/c01-in/roster-beacon). Archives exclude private settings, game data, fetched datasets, diagnostic logs and private history. Original-code MIT licensing and bundled runtime notices remain included. Provider and game-modification disclosures remain in README/About and first-use notice; rights holders can use the repository's Rights concern form. Binaries are unsigned.

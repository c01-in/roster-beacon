# Setup, configuration and recovery

**English** | **[中文技术说明](README.zh-CN.md)**

Only **NBA 2K27 Windows x64 quick play** is supported. Keep the whole portable directory: `_internal` is required. Uninstalling preserves settings and recovery data.

## Normal setup

Choose the game executable (or Find installed game), let the utility find/check existing roster data, choose the current save if more than one is compatible, then Save & get started. SYNC is data the game already created; an empty folder is not a roster. Backup/cache/profile controls are collapsed under Advanced settings. No game is launched by discovery or setup.

Discovery reads installed Steam metadata, local app-ID metadata, bounded Steam userdata/public Documents save locations and known game/app-data subdirectories. Candidate manifest references, ZIP contents and native schemas must validate. A previously configured target or unambiguous current Steam account can resolve a selection; file modification time alone never selects a write target. Unsupported/corrupt candidates are excluded. If no compatible data is found, reach the game menu once, exit, then Find again; manual existing-data selection remains available under Advanced settings.

Normal preference saves preserve the existing immutable recovery copy. A changed game/save/storage/profile binding or explicit re-import creates one from current selected data. Backup/cache namespaces are separated by installation/save identity; existing configured storage paths are preserved for unchanged installations.

## Advanced configuration

| Setting | Purpose |
| --- | --- |
| game_executable | Installed EXE; also identifies a running game |
| launch_mode / steam_app_id | `steam` uses the native Steam URI/discovered App ID; `direct` uses the EXE |
| sync_directory / manifest_name | Actual roster SYNC and manifest for the account you play |
| data_directory | Persistent baselines, backups, logs and last-success record |
| cache_directory | Disposable fetched data/temporary builds; source cache deleted on success |
| baseline_directory | Imported immutable directory identified by manifest hash |
| compatibility_profile | Built-in `nba2k27-rdat-v9`; another JSON does not add another game's support |
| allow_missing_players | `true`: retain original teammates/preserve affected teams and report fallback; `false`: block on unmatched players |
| show_schedule / schedule_team_id | Launch confirmation and reminder team; roster scope remains all 30 teams |
| language | `auto`, `zh-CN`, `en-US` |
| api_base / season_year | Configured HTTPS source; year `0` uses UTC date/July season boundary |
| request_timeout / network_workers | 1–120 seconds / 1–12 concurrent requests |

Use writable locations on your chosen disk. Baselines/backups belong in persistent storage, not cache. Different installations/accounts need separate data directories. `NBA_ROSTER_SYNC_CONFIG` selects another settings file; developers can use an ignored `settings.local.json`. Neither belongs in public artifacts. `--language` or `NBA_ROSTER_SYNC_LANGUAGE` overrides a process; file-picker system buttons follow Windows language.

## Troubleshooting

The game must be closed for sync/restore. A Steam launch request is not proof the game reached its menu. The tool leaves Steam Cloud settings unchanged; Steam in-game adoption remains unverified on a Steam installation.

If cloud/game/another tool changes the manifest, inspect the actual current files and re-import a known-good baseline. Keep recovery materials rather than deleting protection records. For missing players use the [roster-pack workflow](ROSTER-DATA.md).

**Open logs** exposes `app.log`, `last_sync.json`, `启动状态.txt` and backups. The legacy filename is retained. Logs can include private paths/data. Prefer a reviewed GUI diagnostic export or `Roster-Beacon-cli.exe --diagnose`, which omits absolute paths.

Restore references the imported baseline; it does not fetch another official roster. Multiple files do not form a power-loss-proof transaction. After interruption, retain `pending_sync.json`, manifests and roster blobs before troubleshooting.

## Source/build

Use Python 3.12 x64 and pinned requirements. The build script accepts `-BuildRoot`, `-OutputDirectory`, `-Python`, `-PyInstallerRoot`, `-InnoCompiler`. Reuse an installed toolchain and keep build/cache outside source. The GitHub workflow is manual and builds candidates only. Packaging uses an explicit allowlist and excludes personal settings, game data, caches and private Git history.

## First-use acknowledgement

Before provider access or roster-changing operations, read the bilingual source/usage notice and choose Continue or Cancel. Confirmation is saved beside the active settings file as `<settings-stem>.usage-consent.json`, scoped to source/profile/notice revision. Maintenance → About can reopen the notice or reset confirmation. The record is excluded from source/release artifacts and diagnostic summaries. Restores and cached-only operations do not fetch data. Rights-holder contact uses a fixed GitHub issue-form URL from About. Repository setup is a publication task; the application requires no second release to activate its link.

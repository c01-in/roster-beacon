# Roster Beacon

**English** | **[简体中文](README.zh-CN.md)**

> **Supported game: NBA 2K27 on Windows 10/11 x64 — quick play only.**
> Other game editions, consoles and operating systems are unsupported. Steam discovery and launch are implemented; in-game adoption still needs verification on a Steam installation.

Update all 30 teams before playing: transfers, injuries, suspensions, starters and bench order. A failed update blocks game launch. The game can stay disconnected from 2K servers; the computer needs internet access to the configured source.

Current local candidate: **1.0.0-rc8**. No public repository or release has been created. This candidate includes first-use acknowledgement and rights-holder contact/takedown guidance. See [publication status](docs/PUBLICATION.md) and the [implementation and policy findings](docs/legal/IMPLEMENTATION-REVIEW.md).

## Requirements

- Installed **NBA 2K27 Windows x64** and its actual local SYNC directory.
- A compatible native baseline: `manifest_*.bin` and its referenced ZIP containing only `roster.RDAT`, in the supported **unencrypted RDAT v9** layout.
- Permission to use the game, roster data and configured source under their applicable terms.

**No game files or roster/patch pack are included.** The app updates existing uniquely matched records. It cannot create a missing player, portrait, face, model or animation. No particular community download is required; existing compatible native game data is sufficient, with fallback for missing players.

**No additional roster pack is required to use the tool.** SYNC RDAT v9 names the supported game-data format, not a package to install. Use the game's existing compatible native roster even if some current players are absent. If no readable supported native roster exists at all, the operation stops; it does not create a roster from nothing.

## Install and configure

Use the Windows x64 installer or extract the complete portable ZIP, then run `Roster-Beacon.exe`.

1. Open **Settings** and choose **Find installed game**, or choose `NBA2K27.exe` with **Choose game**.
2. The utility searches existing Steam/local save locations and validates native roster data. An unambiguous roster, or the previously configured target, is selected automatically. If several compatible saves remain, choose your current save; last-saved dates help distinguish them.
3. Choose a reminder team, then **Save & get started**. The utility creates its recovery copy and manages storage automatically.
4. On the home page, choose **Update only** or **Update & launch**. The first update asks you to read and accept the source/usage notice. If enabled, confirm the reminder team's previous/next games before launch.

**You do not create a SYNC folder or choose internal storage paths.** SYNC is an existing game-data location, not an application folder. If no valid roster is found, open the game with your Windows account, reach the main menu, exit and choose **Find again**. The utility never creates an empty game-data folder and reports it as a roster.

Backup/cache locations, manual roster paths, import sources and compatibility profiles are under collapsed **Advanced settings**. Normal settings saves retain the original recovery copy. Explicit re-imports or a changed installation/storage binding establish a new copy while retaining old backups. This does not change the all-team update scope or runtime integrity checks.

The installer installs only this utility. It does not install a pack, download the game or start it automatically. Each computer/account needs its own settings.

## Missing players and compatible packs

The home page shows coverage from the **last successful update**. **Update & fallback details** lists absent/ambiguous source records, retained teammates, preserved teams and deferred source records. Updated counts exclude preserved teams and deferred players. Strict mode still blocks an update with missing players.

Default fallback uses the **recognized roster installed immediately before the update**, not the older recovery baseline. It first updates real matched players, then fills gaps with existing real teammates not assigned elsewhere. Retained players keep their identity and original data, including availability. If no source players match a team, or a safe five-position lineup/capacity cannot be formed, that team's entire existing roster, lineup and player records are preserved. Transfers involving preserved teams are deferred as needed to prevent duplicate ownership; this can require preserving another affected team. Known Out/suspended retained players are excluded from newly built lineups. An unchanged preserved team remains a previous snapshot, not a claim of current availability.

Input/source corruption and incompatible data still stop the update. Runtime read-back checks verify duplicate-free ownership and exact preservation of protected records.

To include new players, obtain a compatible update you are authorized to use, install it through its supported process with the game closed, then re-import the **current actual game SYNC** and sync again. **Maintenance → Game roster & fallback** explains this path. Names-only lists, mappings, portraits and models cannot supply missing player records. Newer data does not establish compatibility or redistribution rights. Read [roster data and missing players](docs/ROSTER-DATA.md).

## Behavior and recovery

- Assigns five distinct starters by position/depth chart and a bench by depth/position, up to 15 active players. In-game coaching controls substitutions.
- Excludes Out/suspended players from active rotation; other availability states follow the source.
- Checks format, layout and written data. Unknown layouts, failed requests and unexpected manifest changes stop the write/launch workflow.
- Deletes source cache on success; retains failure evidence, baselines and manifest backups.
- Provides baseline restore and diagnostic export under **Maintenance**. Uninstalling preserves settings/recovery data.
- Does not support MyCareer, MyNBA/franchise/season saves or live in-game updates.

The default source is ESPN's publicly reachable endpoint, **not the official 2K daily roster and not an open-data license**. Reachability does not establish permission; provider terms remain an unresolved publication item. No NBA, 2K, Take-Two, Valve or ESPN affiliation is claimed.

## Data source, local requests and usage risks

The default source is **ESPN**, accessed automatically from the user's computer for rosters, injuries, rotations and fixtures. Requests are not routed through a Roster Beacon server. A configured alternative URL is shown in the notice; it must support the expected data schema. This is not an official NBA/2K roster feed.

- **Data access:** ESPN's applicable terms restrict automated extraction without express permission; the project has not obtained such permission. [Provider terms](https://disneytermsofuse.com/english/).
- **Game edits:** Take-Two terms restrict external game modifications and certain related tools, subject to their stated exceptions. Contract disputes, takedown requests or account measures may arise. [Publisher terms](https://www.take2games.com/legal/en-US/).

Before the first data request or roster-changing operation, a modal explains the source, local requests and these risks. The user chooses **I understand — continue** or **Cancel**. Cancellation stops the operation before fetching data, writing the roster or launching the game. Acceptance is stored locally for this configuration, source, compatibility profile and notice revision. Changes to those values require confirmation again. **Maintenance → About → Source & risks** reopens the notice; **Reset confirmation** revokes the saved acknowledgement. Cached-only operations and baseline restores do not fetch data.

Acknowledgement records the user's voluntary choice; it does not provide permission from ESPN or the publisher. This utility is independent and makes no claim of account safety or third-party approval.

## Language, configuration and development

The app follows Windows display language: Chinese for Chinese display languages, English otherwise. The bottom-left selector overrides it while preserving paths, unsaved fields and form position.

Settings: `%APPDATA%\NBA-Roster-Sync\settings.json`; `NBA_ROSTER_SYNC_CONFIG` selects another file. Language: `auto`, `zh-CN` or `en-US`; `--language` overrides a process. Console options include `--settings`, `--launch`, `--update-only`, `--restore`, `--diagnose` and `--import-baseline`.

The legacy configuration directory/environment prefix is retained under the Roster Beacon name so existing settings and recovery materials continue to work.

- [Setup and recovery](docs/SETUP.md) · [documentation index](docs/README.md)
- [Publication plan](docs/PUBLICATION.md) · [name candidates and similar projects](docs/NAME-REVIEW.md)
- [Contributing](CONTRIBUTING.md) · [security](SECURITY.md) · [release notes](RELEASE_NOTES.md)

Source requires Windows, Python 3.12 x64 and `requirements.txt`; run `python app_main.py`. `scripts/build_windows.ps1` uses existing PyInstaller/Inno Setup with explicit cache/output paths. The manual GitHub workflow builds without publishing. Publish from a clean allowlisted export, not the private working repository's history.

## License

[MIT](LICENSE) applies to original contributor-owned code/artwork. It does not license game content, proprietary packs, third-party expression, provider content or trademarks. [Third-party notices](THIRD_PARTY_NOTICES.md) identify dependencies and the documented format-reference provenance. Credit/disclaimers do not grant missing permissions. This candidate has **not** been declared rights-cleared for public distribution.

## Rights-holder contact and takedown handling

Rights holders and authorized representatives can use the **Rights concern / takedown request** issue form to contact the maintainer. Identify the affected feature, file, URL or release, the rights or terms concerned, and the requested action. Keep confidential evidence and personal details out of public issues.

[Submit a rights concern / takedown request](https://github.com/c01-in/roster-beacon/issues/new?template=rights_concern.yml). The same contact route is available from **Maintenance → About → Rights contact**.

On receiving a rights concern, we will prioritize pausing the affected distribution or functionality while reviewing it, and promptly remove, restrict or correct the relevant material as appropriate. This covers releases and downloads we control; it cannot recall copies already downloaded. Cooperating with a takedown request does not grant third-party permission or guarantee immunity from liability.

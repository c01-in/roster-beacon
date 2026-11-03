# 1.0.0-rc8 — Windows prerelease

**English** | **[简体中文 README](README.zh-CN.md)**

**NBA 2K27 / Windows 10–11 x64 / quick play only.** Independent utility, not an official roster release. Other game editions/platforms are unsupported. Steam in-game adoption still needs on-device verification.

## Changes

- Normal setup now needs only the game executable, an existing-roster choice when ambiguous, and Save & get started. Storage/profile fields are collapsed under Advanced settings.
- Automatic discovery validates local roster data, supports Steam/manual EXE selection, retains current bindings and separates new installation storage.
- Normal preferences preserve the recovery copy; explicit re-import creates a new one and retains older copies.
- Rights contact uses the final fixed About link. Repository creation/Issues setup is sufficient; the same binary uses its final contact URL without a follow-up activation release.

- Shared first-use source/risk confirmation before automatic requests or roster writes, with explicit cancellation, locally stored acknowledgement and reset from About.
- English/Chinese README and About explain ESPN local requests and external-game-modification risks, plus a prepared rights-holder contact and prompt pause/takedown process.
- Long modal text scrolls within the screen while action buttons remain available. New dialogs have not been exercised in an isolated UI environment.

- Clarify that RDAT v9 is a format, not a required extra pack. Existing compatible game data can be used with fallback.
- Fill gaps with real original teammates; preserve entire teams with no matches, unsafe lineups or capacity conflicts. Defer related transfers to prevent duplicates.
- Plan against the recognized currently installed roster, fingerprint protected records and recheck the manifest before commit. Strict mode and invalid/source data still stop updates.
- New fallback paths have not been exercised in-game or through desktop UI; this candidate is built without automated tests or changes to the user's roster.
- Default English README, prominent Chinese switch, English contribution/security/data notices and issue/PR templates.
- Explicit supported game/platform/mode in README, home, Settings and About.
- Partial-coverage status with a scrollable unmatched-player list.
- Authorized local roster update and current-SYNC re-import guide. No pack download, redistribution or player/model creation.
- Supported unencrypted SYNC parser retained; unused encrypted-save/cipher-key branch removed.
- Independent rights review and explicit OpenSSL notices. rc4 wheel isolation retained.

## Candidate artifacts

- `Roster-Beacon-1.0.0-rc8-windows-x64-setup.exe`
- `Roster-Beacon-1.0.0-rc8-windows-x64-portable.zip`
- `Roster-Beacon-1.0.0-rc8-source.zip`
- `SHA256SUMS.txt` and `release-manifest.json`

The installer installs only the utility. Users supply their own compatible local baseline/settings. Artifacts exclude proprietary data, private configs, share credentials and private repository history.

## Distribution and notices

Public source: [c01-in/roster-beacon](https://github.com/c01-in/roster-beacon). This prerelease includes the accepted Windows build and accompanying source, checksums and license notices. Local settings, consent records, game files, fetched datasets, diagnostic logs and private Git history are excluded.

The source/provider and game-modification considerations remain disclosed in README/About and the first-use notice; publication does not claim provider permission or legal clearance. Rights holders can use the repository's Rights concern issue form. Binaries are unsigned; Steam in-game adoption and a fully isolated UI walkthrough remain outside the recorded agent validation. The manual GitHub workflow builds only when requested and does not publish automatically.

# Changelog

**English** | **[简体中文](docs/zh-CN/CHANGELOG.md)**

## 1.0.0-rc10 — 2026-11-03

Automatically adopt a valid roster changed by a game/patch at the configured save location. Validate and build against the current roster, preserve its complete manifest/blob recovery copy, then commit normally. Keep original recovery baselines and old backups. Invalid/incompatible data, another installation binding, backup failures, a running game or changes during synchronization still stop safely. Manual re-import is optional rather than required for routine patches. Update bilingual in-app guidance.

## 1.0.0-rc9 — 2026-11-03

Fix updates blocked by partial ESPN depth charts (observed: Denver returned only PF/C). Default fallback fills missing source positions using actual native player positions and the previous starting-five role mapping, preferring previous local order. Transfers and injuries still update for safely planned teams; unsafe teams preserve all existing records and related transfers remain deferred. Same-position duplicates keep their first source occurrence. Wrong team/season, invalid records, absent whole depth charts and strict-mode missing positions still block updates. Bilingual coverage details identify the missing positions and local fallback. Diagnostic source responses remain on failure and clear only after a successful commit.

## 1.0.0-rc8 — 2026-11-03

Replace the directory-heavy setup with game selection, automatic existing-roster discovery/validation and Save & get started. Steam and manual EXE selection share discovery, with explicit ambiguity handling and readable save timestamps. Internal directories and profile/import controls move into collapsed Advanced settings. Normal preference saves preserve the recovery baseline; changed bindings or explicit re-import create a new recovery copy without deleting old backups. Rights contact is a fixed, clickable About link; no post-publication build or activation flag is required. Discovery was exercised read-only on the owner's existing data; no game, desktop UI or automated application tests were run.

## 1.0.0-rc7 — 2026-11-02

Add shared first-use acknowledgement before provider requests or roster changes, including direct/CLI entry points. Store confirmation locally by configuration, source, profile and notice revision; cancellation blocks fetching, writes and launch. Maintenance/About shows both risks with notice/revocation actions. English/Chinese README documents local ESPN requests, voluntary use and rights-holder contact/takedown handling; add a prepared rights-concern issue form. Long dialogs keep controls visible with scrollable text. Source-provenance findings are now specific and evidence-backed. No desktop UI, game or automated application tests were run for this candidate.

## 1.0.0-rc6 — 2026-11-02

SYNC RDAT v9 is a native format, not a required pack. Missing-player fallback keeps real current teammates; teams with no matches, unsafe lineups or capacity conflicts preserve entire pre-update records. Related transfers are deferred to avoid duplicate ownership. Planning uses the recognized installed roster; the imported baseline stays for recovery. Protected records receive exact fingerprint checks. UI/logs distinguish preserved data from updates. Strict mode and source/integrity failures still block updates. No game or desktop UI is operated during this build.

## 1.0.0-rc5 — 2026-11-02

English-first repository content with Chinese switching links. Explicit NBA 2K27 Windows x64 quick-play scope. Last-success coverage details and authorized local roster/re-import guidance. Unused encrypted-save support removed. Independent rights review and explicit OpenSSL notices added. No public release; working name retained pending selection.

## 1.0.0-rc4 — 2026-11-02

Scoped settings wheel bindings replace global interception. Dropdowns scroll independently; closed selectors retain values. Language switches preserve form position.

## 1.0.0-rc3 — 2026-11-02

Fixed desktop sidebar replaces hero/tabs. Consistent dark controls/fonts, fixed save action and system-DPI-aware packaging.

## 1.0.0-rc2 — 2026-11-02

Chinese/English interface, Windows language detection, manual override and original geometric artwork.

## 1.0.0-rc1 — 2026-11-02

Local Windows publication candidate: GUI configuration, Steam discovery/launch, immutable baseline import, recovery, diagnostics, installer/portable/source packaging and explicit source allowlisting. All-team updates, launch blocking and cache cleanup retained. The local reinstall/game workflow does not establish every Steam/game-version combination.

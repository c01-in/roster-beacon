# Public repository preparation

**English** | **[中文 README](../README.zh-CN.md)**

## Prepared content

- `README.md` is English; its first line after the title offers **简体中文**. `README.zh-CN.md` links back.
- English-facing release notes, changelog, contribution/security guidance, third-party notices and issue/PR templates.
- Explicit **NBA 2K27 / Windows 10–11 x64 / quick play only** support statement in README and the app.
- Local-baseline/authorized-pack workflow and missing-player limitations.
- Separate rights audit and name-search record.

## Draft GitHub metadata

| Field | Prepared value |
| --- | --- |
| Owner account discovered | `c01-in` |
| Visibility | **Public** |
| Repository name | `roster-beacon` — owner selected Roster Beacon |
| Description | Windows roster updater for NBA 2K27 quick play: team assignments, injuries and rotations from a compatible local SYNC baseline. |
| Topics | `nba2k27`, `windows`, `basketball`, `roster`, `python` |
| Default documentation language | English, with prominent Simplified Chinese links |
| Public repository / release URL | Not created; publication explicitly on hold |

The local working repository has no remote. The owner selected Roster Beacon, then explicitly chose **finish a local candidate and resolve rights before publication**. No public repository, placeholder destination, tag or release has been created.

The owner subsequently requested clear README/About disclosures, first-use voluntary acknowledgement, and rights-holder contact with prompt pause/takedown handling. rc7 implements those safeguards without treating acknowledgement as provider/publisher permission. Public repository creation and publication have not been requested by that implementation change.

The prepared contact route is the **Rights concern / takedown request** issue form at `.github/ISSUE_TEMPLATE/rights_concern.yml`. When creating the public repository, enable Issues and confirm the form is available before announcing downloads. Its intended URL is `https://github.com/c01-in/roster-beacon/issues/new?template=rights_concern.yml`; the final contact URL is already built into the application, without a post-publication feature flag. Creating the repository and enabling Issues makes the same binary link usable; it does not require another application release. The repository has not been created yet; verify the form before announcing public downloads. No private email address is invented.

## Rights work that remains open

The [implementation follow-up](legal/IMPLEMENTATION-REVIEW.md) records actual pinned code comparisons and independently verified game enum facts. No copied implementation was identified in the scoped shipped files; the old generic upstream-provenance concern is narrowed accordingly. Provider terms and external-game-modification clauses remain separate considerations. The encrypted-save branch was removed from rc5. No provider permission or publisher-specific external-editor authorization was obtained, and no blanket finding that this project or modding tools are illegal is made. Public availability, offline use and disclaimers alone do not establish authorization.

The historical third-party roster package has no verified distribution permission. It remains excluded from source, installer and release assets, together with private configs, baseline/saves, share credentials and private Git history. Original artwork/owned code and third-party content have separate rights.

## Concrete next publication step

After the unresolved rights items are addressed and the owner resumes publication, create the **public** `c01-in/roster-beacon` repository using the clean exported source, apply the English metadata, and review both README languages there. Keep game data out of Git. The manual workflow builds without publishing. No external message or rights-holder contact has been sent.

This record is local preparation, not a claim that remote files, repository settings, tags or releases already exist.

Roster Beacon retains the legacy `%APPDATA%\NBA-Roster-Sync` settings identifier and environment-variable prefix. The installer keeps its existing application ID; known old executable names are retired on an upgrade. No existing installation was changed by preparing this candidate.

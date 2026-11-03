# Repository and release maintenance

**English** | **[简体中文 README](../README.zh-CN.md)**

- Public repository: [c01-in/roster-beacon](https://github.com/c01-in/roster-beacon).
- Description: Windows roster updater for NBA 2K27 quick play: team assignments, injuries and rotations from compatible local game data.
- Supported target: NBA 2K27, Windows 10/11 x64, quick play. Other editions are unsupported; Steam in-game adoption remains unverified.
- Documentation defaults to English with a prominent Chinese README link.
- Original contributor-owned code/artwork uses MIT; third-party runtime notices are retained separately. Game assets, roster packs and provider content are excluded.

## Publication content

Publish only the allowlisted clean source and generic contributor commit history. Exclude local configuration/consent records, original private history, native roster/save packages, fetched data, machine diagnostics, share credentials and personal identifiers. Release metadata and checksums accompany the accepted build.

The source/provider and external-game-modification considerations remain documented in README/About, the first-use notice and [implementation findings](legal/IMPLEMENTATION-REVIEW.md). Publishing is not a claim of provider/publisher permission or a determination of legal liability.

## Contact and release handling

Enable Issues with the prepared Rights concern / takedown request form. Enable private vulnerability reporting for confidential security reports. The fixed rights-contact URL is already included in rc8; no activation build is needed.

On receiving a rights concern, prioritize pausing affected distribution/functionality, review it and promptly remove, restrict or correct affected material as appropriate. Track takedown requests without placing personal or confidential evidence in public issues.

Publish reviewed Windows packages as prereleases until the intended support/validation status justifies a stable version. The manual build workflow has read-only repository permissions, runs on request and does not publish automatically. Keep checksums, actual code provenance, platform limits and runtime notices accurate for each release.

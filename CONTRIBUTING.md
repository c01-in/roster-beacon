# Contributing

**English** | **[简体中文](docs/zh-CN/CONTRIBUTING.md)**

Supported target: **NBA 2K27 / Windows x64 / unencrypted native SYNC RDAT v9 / quick play**. Relabeling a profile does not add support for another game.

Explain the concrete problem, final behavior, actual validation and limits. Format work needs real schema and field-semantics evidence. Preserve integrity checks, recovery data, failure-blocked launch, partial-coverage reporting and dropdown wheel isolation. Do not fabricate players or disable checks to make an update appear successful.

The maintainer's current workflow uses focused manual review and real build/runtime evidence, without requiring an automated test suite. Never report an unperformed check as passed.

Public issues/PRs must exclude game files, proprietary rosters, personal settings, private paths, account IDs, sensitive logs and share credentials. Use a reviewed diagnostic summary. New dependencies require version, provenance and redistribution terms. Update both README languages when behavior changes. Add public files to the packaging allowlist deliberately.

Read [roster data](docs/ROSTER-DATA.md), [publication status](docs/PUBLICATION.md) and the [rights review](docs/legal/RISK-REVIEW.md) before proposing a dataset, pack or provider integration.

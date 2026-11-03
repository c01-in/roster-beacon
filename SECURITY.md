# Security and privacy

**English** | **[简体中文](docs/zh-CN/SECURITY.md)**

The utility does not request Steam/2K passwords or API keys, inject into the game, patch its EXE, change drivers/anti-cheat or modify Steam Cloud settings. Supported input is an unencrypted local NBA 2K27 SYNC roster; encrypted saves are rejected.

It reads/writes selected roster data and stores recovery materials locally. HTTPS requests go to the configured provider, which can observe normal connection metadata such as IP address. There is no app telemetry service or automatic executable updater.

Settings/logs may expose private details. Diagnostic export omits absolute paths, but inspect any file before sharing. Do not attach game files, packs, saves, account identifiers or extraction credentials to public issues.

A repository/private security-reporting channel has not been configured yet. Until then, use a maintainer-provided private channel for sensitive reports instead of posting private data or exploit details publicly. This is not an account-safety guarantee. Separate provider/legal questions are covered in the [rights review](docs/legal/RISK-REVIEW.md).

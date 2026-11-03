# Security and privacy

**English** | **[简体中文](docs/zh-CN/SECURITY.md)**

The utility does not request Steam/2K passwords or API keys, inject into the game, patch its EXE, change drivers/anti-cheat or modify Steam Cloud settings. Supported input is an unencrypted local NBA 2K27 SYNC roster; encrypted saves are rejected.

It reads/writes selected roster data and stores recovery materials locally. HTTPS requests go to the configured provider, which can observe normal connection metadata such as IP address. There is no app telemetry service or automatic executable updater.

Settings/logs may expose private details. Diagnostic export omits absolute paths, but inspect any file before sharing. Do not attach game files, packs, saves, account identifiers or extraction credentials to public issues.

Use GitHub's [private vulnerability reporting](https://github.com/c01-in/roster-beacon/security/advisories/new) for sensitive security reports. Use the [Rights concern form](https://github.com/c01-in/roster-beacon/issues/new?template=rights_concern.yml) for non-confidential rights/takedown requests. Keep personal details, secrets and game files out of public issues. This is not an account-safety guarantee. Separate provider/legal questions are covered in the [rights review](docs/legal/RISK-REVIEW.md).

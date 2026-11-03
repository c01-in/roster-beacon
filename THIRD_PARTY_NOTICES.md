# Third-party notices and rights boundaries

**English** | **[简体中文](docs/zh-CN/THIRD_PARTY_NOTICES.md)**

[MIT](LICENSE) covers original contributor-owned code and geometric artwork. It does not grant rights to game assets, proprietary rosters, external datasets, trademarks or third-party expression without permission.

## Runtime components

Windows builds include Python (PSF and bundled notices), psutil (BSD-3-Clause), Tcl/Tk (their respective licenses), and PyInstaller's bootloader (GPL with its application-distribution exception). Python's combined license already includes Tcl and other terms. Python HTTPS uses OpenSSL; the reviewed local runtime is **OpenSSL 3.0.16**, under Apache-2.0. The matching upstream license/attribution in `licenses/` is copied into distributions alongside collected runtime notices. A different runtime needs matching notices.

- [Python license](https://docs.python.org/3/license.html)
- [psutil](https://github.com/giampaolo/psutil)
- [PyInstaller licensing and exception](https://pyinstaller.org/en/stable/license.html)
- [OpenSSL 3.0.16 license](https://github.com/openssl/openssl/blob/openssl-3.0.16/LICENSE.txt)
- [Tcl license](https://www.tcl-lang.org/software/tcltk/license.html)

Actual bundled DLLs and their applicable notices remain part of distribution review. A component list does not replace license obligations.

## Format references

The container implementation acknowledges [u5ur/2K-Unpack-Save](https://github.com/u5ur/2K-Unpack-Save). Earlier read-only diagnostics referenced [discobisco/2k26-Editor](https://github.com/discobisco/2k26-Editor). The [pinned source comparison](docs/legal/IMPLEMENTATION-REVIEW.md) found no copied implementation in the scoped public modules. The shared 157-entry injury table was independently confirmed, including order, as the local game's native enum identifiers. These credits document format research and compatibility facts; they do not claim an upstream license, publisher approval or rights to ship game content. Actual incorporation of third-party implementation would require its applicable rights basis.

The old memory tool is excluded. rc5 removes the unused encrypted-save branch and hardcoded cipher key, retaining only the supported unencrypted SYNC path. This does not settle remaining provenance or game-contract questions.

## Data and branding

ESPN's reachable endpoint is the configured source, not an official 2K feed or an open-data license. [ESPN's terms entry](https://support.espn.com/hc/en-us/articles/360035445091-Terms-of-Use) points to [Disney terms](https://disneytermsofuse.com/english/), including automated-extraction restrictions. No provider permission has been obtained. Fetched datasets, proprietary packs, game models, portraits and saves are excluded.

NBA, NBA 2K27, 2K, Take-Two, Valve and ESPN names describe compatibility/source context. No affiliation, endorsement, trademark permission or publisher approval is claimed. Small basketball/app icons are original MIT geometry; no league/team logos or player photos are used. See [artwork provenance](assets/README.md).

Read the [independent pre-publication review](docs/legal/RISK-REVIEW.md). The candidate has not been declared rights-cleared.

# README visuals and screenshot provenance

## Original artwork

`hero.svg`, `download-installer.svg` and `download-portable.svg` are original project SVG geometry and typography under the root MIT license. They use system font fallbacks, not bundled font files. No external images, fonts, scripts, player likenesses or league/team logos are embedded. The hero is decorative artwork, not a fabricated application screen or live statistic.

## Native application captures

The six PNG files are actual rc8 application-source/native-Tk window renders, captured on 2026-11-03 using an independent Windows desktop object. It was never switched to the user's input desktop. No keyboard/mouse input was injected, no game was launched, no data-provider request was made, and the user's original configuration/game data was not written. This is desktop/input separation for documentation rendering, not a filesystem/network virtual machine.

| Files | Real state shown | Privacy/context treatment |
| --- | --- | --- |
| `setup-en.png`, `setup-zh.png` | First-use Settings with Advanced settings collapsed | An isolated, unconfigured local settings file; no personal paths or accounts shown |
| `update-en.png`, `update-zh.png` | Existing successful local result: 30/30 teams, 516/521 matched source players, 92 reports | Only the actual summary region was captured; the path-containing connection panel is excluded |
| `matchup-en.png`, `matchup-zh.png` | The saved previous/next fixtures from that run, replayed through the actual themed schedule dialog | Existing recorded fixture facts, not a fresh fetch or live schedule; Pacific time |

The saved source snapshot was fetched at `2026-11-03T05:07:38.020614+00:00` (November 2, 2026, 21:07 Pacific). Counts and fixture examples are historical, not promises for another roster or a current update. No successful result was invented, and no generated image/inpainting was used to reconstruct an application screen. PNGs contain no added author/path metadata. Original settings, full reports, desktop handles and capture logs are kept outside the public repository.

The application's original UI artwork is covered by MIT. Screenshots are documentation of that UI; third-party names and factual fixture/status examples are descriptive compatibility/source context, not a claim to license game/provider content or marks. See the root third-party notices and usage-risk section.

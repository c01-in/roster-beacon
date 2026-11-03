# Before public distribution

**Roster Beacon publication is on hold at the owner's request.** The review does not establish infringement, clearance or a legal opinion. Track the actual rights basis instead of relying on acknowledgements or a disclaimer.

| Item | What would resolve it | Current position |
| --- | --- | --- |
| Format-reference provenance | Keep pinned comparisons and independently verified native format/enum facts; check permissions if upstream implementation is actually incorporated later | Scoped source review completed: no copied implementation identified; all 157 enum entries independently confirmed. See IMPLEMENTATION-REVIEW.md |
| ESPN/provider use | Obtain written permission or licensed terms covering this automated use, or implement a provider adapter for a source with suitable rights | Open; public HTTP reachability is insufficient |
| Game modification/format | Account for 2.3/6.4 restrictions on external modification and certain tool distribution, their exceptions and 6.7 consequences; preserve local quick-play scope | Concrete contractual exposure remains; no NBA-2K27-specific external-editor permission established. This is not a finding that the project is illegal or that modding forums must close |
| Old roster pack | Verifiable authorization from relevant rights holders covering intended distribution | No verified grant; pack/share credentials excluded |
| Runtime notices | Preserve notices matching the actual Python/OpenSSL/Tcl/Tk/psutil/PyInstaller and other bundled components | Explicit OpenSSL 3.0.16 license/attribution added; further builds record their actual TLS version |
| Branding | Use Roster Beacon with descriptive NBA 2K27 compatibility text, original artwork, and appropriate naming review | Owner selected; preliminary name search is not formal trademark clearance |

The encrypted-save branch and hardcoded game cipher key have been removed. This is a concrete mitigation, not a substitute for resolving the remaining items.

The owner requested rc7 source/risk disclosures in both READMEs and About, first-use voluntary acknowledgement before requests/roster changes, and a rights-holder contact and prompt pause/takedown process. These are now implemented as product controls and communication policy. They do not establish provider permission or a legal finding of liability. The contact issue form becomes active when the public repository/Issues are enabled; no external notice has been sent.

## Information to request from upstream maintainers

The scoped follow-up records the pinned sources and actual common metadata. It found no copied implementation in the reviewed public modules. A blanket upstream-permission request is therefore not an established prerequisite merely because the implementation refers to format research. If a later change includes upstream implementation or expressive documentation, identify the exact material and obtain its applicable license/permission before distribution. No maintainer has been contacted.

## Information to request from a data provider

Describe the actual on-demand roster, injury, depth-chart and schedule retrieval; the intended free/public client distribution; local caching/deletion; and whether results are redistributed. Obtain terms covering access method, rate, caching, display, attribution and geographic limits. The current configurable base URL expects the existing source schema; switching providers can require a genuine adapter, not only a URL change. No provider permission has been obtained or request sent.

Do not upload proprietary game/roster files to public issues to resolve these questions. Keep permissions with their actual scope, version/date and granting party. Resume repository/release publication only when the owner decides these items have been addressed.

# Implementation and modding-policy findings

Reviewed on **2026-11-02**, against application revision `6cbcedc`. This records concrete source and policy findings. It is not a ruling on infringement or a guarantee of legal clearance. The earlier publication hold was the owner's instruction; it is not a legal prohibition imposed by the assistant.

## Code and compatibility data

The reviewed public allowlist contains **19 Python files**. These were compared with the unpacker and eight relevant editor implementation files. Exact matching blocks after trimming whitespace and AST comparisons supplemented manual review; the only two-line matches were a docstring terminator followed by the standard future-annotations import. No identical nontrivial function or copied implementation block was identified in this scope. Such comparisons cannot prove the complete historical origin of independently rewritten code.

References were pinned to:

- [`u5ur/2K-Unpack-Save`, `3d28629f2cb254077e910439d0065ad50ee6c2d8`](https://github.com/u5ur/2K-Unpack-Save/tree/3d28629f2cb254077e910439d0065ad50ee6c2d8): `UnpackSave.py`.
- [`discobisco/2k26-Editor`, `08cb0098b606499b1f0ed87c5a2ef49a7f2d5b61`](https://github.com/discobisco/2k26-Editor/tree/08cb0098b606499b1f0ed87c5a2ef49a7f2d5b61): `core/field_io.py`, `core/addressing.py`, `models/schema.py`, `core/conversions.py`, `core/offsets.py`, `core/base_scanner_2k27.py`, `core/nba2k27_hook.py`, and `memory/read_buffer.py`.

The unpacker's `parse_bundle` shares the necessary BNH/BNDL layout facts: 24-byte bundle headers, 60-byte node headers, field offsets and eight-byte alignment. The current implementation uses a different supported container version, validates bounds and checksums, rejects encrypted files and implements in-place-capacity reconstruction. The reference's Blowfish implementation, key schedule, decryption/export functions and command-line flow are absent from the current public modules. Its node parser is not imported or executed.

The shipped `injury_types.json` is **exactly the same 157-entry sequence** as the editor's `Players.Vitals.Health[1].versions.2K27.values` and the corresponding second injury selector. This is a concrete shared metadata item, not evidence that the whole application was authored without references.

It was then independently checked against the owner's local game executable, opened read-only: the `PLAYERDATA_INJURY` marker occurs at byte **97,211,197** in the **880,513,304-byte** executable; all following 157 NUL-separated identifiers and their order match. SHA-256 of those identifiers joined by NUL is `76d62cb38f09866b8a3f9c7860f240bd12b898e921d7a1e6249bad6b5cf971c6`. No game executable, extracted symbol block or roster is distributed as evidence.

This establishes the table's role as native compatibility identifiers and ordering, rather than an editor author's invented medical database. U.S. copyright guidance distinguishes methods/systems, names and short phrases from protected original expression. That supports treating the observed format facts and native identifier mapping separately from copying an upstream implementation; it does not settle game-contract restrictions or every territory's database rules. [Copyright Office Circular 33](https://www.copyright.gov/circs/circ33.pdf).

**Scoped conclusion:** no copied upstream implementation has been identified in the shipped files reviewed. The earlier generic statement that both upstreams necessarily require a redistribution grant for this entire application is unsupported by the comparison. Keep format credits and this factual provenance record; revisit an upstream license if actual upstream implementation or expressive documentation is later incorporated.

## What the actual tool does

- `sync_nba.py` changes a user's existing roster ZIP and local manifest while the game process is closed, with backups and runtime integrity checks.
- `save_container.py` accepts supported unencrypted SYNC data and rejects `EBNH`; it carries no game-container decryption implementation or key.
- The public allowlist excludes `inspect_roster.py`, old memory diagnostics, proprietary roster packages, baselines, saves and fetched snapshots. Game-process detection is not memory injection.
- `roster_file.py` reads schemas contained in the user's own roster; it does not patch a game executable. Checksums are recomputed for edited records. These facts alone do not decide the legal classification of an integrity/access-control mechanism.
- The target is local quick play. The tool does not implement VC manipulation, paid-content unlocking, multiplayer cheats or anti-cheat bypasses. It also does not force Steam/the game into offline mode, so this scope is not a promise of account safety if users later enter online modes.
- `fetch_source.py` makes automatic ESPN HTTP requests, and `schedule_notice.py` retrieves schedules through that source. User-local requests remain automated requests.

## How far Take-Two's restrictions extend

The current [Take-Two terms](https://www.take2games.com/legal/en-US/) reach beyond online cheating:

| Provisions | Reach |
| --- | --- |
| 2.3 / 6.4(4) | External modification/reverse engineering, subject to stated permission/legal exceptions. |
| 5.3 | Recognizes editing with publisher-provided tools; no blanket external-editor permission. |
| 6.3(1) | Unfair advantage, interference and unentitled content access. |
| 6.4(3)/(5) / 6.5 | Certain tool provision and support for violations. |
| 6.7 | Possible progress/account/service measures and legal action. |

Our inference: local SYNC edits retain contractual exposure. No NBA-2K27-specific exception was established. This is not a court finding, a prediction of enforcement, or a rule automatically closing independent forums. Applicable law and actual conduct remain relevant.

## Why public modding tools and forums exist

- The same publisher expressly welcomes and explains modding for **XCOM 2**. This is direct evidence that a general Take-Two restriction is not a reason to classify every modification tool as forbidden. That game's policy does not transfer to NBA 2K27. [2K's XCOM 2 modding guidance](https://support.2k.com/hc/en-us/articles/216138438-XCOM-2-Modding).
- WeMod publicly lists NBA 2K trainers. This verifies that examples exist; its listing does not establish what permission it has or why a rights holder has or has not acted. [Provider's franchise page](https://www.wemod.com/franchises/nba-2k).
- Nexus Mods operates a submission policy that addresses permissions, attribution, per-file moderation and rights-holder reports, rather than declaring all modding prohibited. [Nexus submission rules](https://help.nexusmods.com/article/28-file-submission-guidelines).
- U.S. section 512 supplies conditional hosting-liability limitations and a notice/counter-notice process. A platform's ability to host user submissions and process individual complaints is a different question from the merits of an individual tool. This is not a claim that any particular NBA forum qualifies for a safe harbor or that every jurisdiction follows the same rules. [Copyright Office section 512 explanation](https://www.copyright.gov/512/).

The NLSC main/forum pages returned HTTP 403 during this review. Their specific policies and any private publisher arrangements were not verified. No inference about their permission or enforcement history is presented as fact.

## Practical project position

The code comparison supplies no basis to abandon the project as a copied-code product. Its local-roster purpose also should not be collapsed into online cheating. Continue treating it as an independent local quick-play utility, distribute original tool code and licensed runtimes rather than game/roster packages, and preserve the narrow compatibility scope.

The ESPN access terms and the external-game-modification clauses remain separate release considerations. The current [Disney terms, 2.B.x](https://disneytermsofuse.com/english/) restrict automated extraction without their express written permission; replacing that source with one whose terms cover the actual automated use is an actionable development route. Changing the URL alone is insufficient when a new provider has a different schema. No suitable replacement is claimed to have been implemented by this review, and the user's automatic injury/transfer/rotation requirements are unchanged.

This review made no runtime/UI/game changes, ran no automated application tests, contacted no third party and published nothing. Machine-readable comparison results accompany the report; temporary downloaded reference files are not included in the public export.

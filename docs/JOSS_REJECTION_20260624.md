# JOSS Submission — Desk-Rejected 2026-06-24 (record + next-venue analysis)

> Submission: pyobfus v0.5.1 → JOSS, pre-review issue `openjournals/joss-reviews#10788`.
> Submitted 2026-06-22; desk-rejected 2026-06-24 by Managing EiC **Daniel S. Katz**.
> Paper source: `paper/paper.md` + `paper/paper.bib`. Tracking: `docs/POST_V0.4_TODO.md` §Distribution.

## 1. What happened (timeline of issue #10788)

| When | Event |
|---|---|
| 2026-06-22 | Submitted (v0.5.1, Subject: Software engineering, financial COI disclosed in notes-to-editor) |
| 2026-06-23/24 | editorialbot auto-checks — **all passed**: refs clean (1 OK DOI, 3 no-DOI SKIP = normal for packages/specs, 0 missing/invalid); paper 1462 words with all 6 required sections (Statement of need / State of the field / Software design / Research impact / AI usage disclosure); repo analysis posted |
| 2026-06-24 | Managing EiC **desk-rejected** (`@editorialbot reject`), issue closed |

## 1b. Official submission record (from JOSS dashboard, joss.theoj.org)

Confirmed status on the JOSS site: *"This paper is rejected which means it has not been accepted into The Journal of Open Source Software."* · Submission type: **New submission** · Submitted **22 June 2026**. Author: `zhurong0525@gmail.com` / GitHub `@zhurong2020` · Published papers: **0**.

**Notes to editor (verbatim — the COI + prior-publication disclosure as submitted):**

> Software (brief): pyobfus is an open-source, AST-based Python obfuscator whose distinguishing feature is a reverse stack-trace mapping workflow that keeps obfuscated code debuggable by developers and AI assistants; its tools are exposed through a JSON CLI and a Model Context Protocol server.
>
> Prior/planned publication: No portion of this submitted work (paper, code, or documentation) has been published or submitted to, or is planned for, another peer-reviewed venue.
>
> Conflict of interest (financial): I disclose a financial interest. pyobfus follows an open-core model: the Community Edition described in this paper is fully open source (Apache-2.0) and self-contained, while a separate Professional Edition is a commercial product that I develop and license. A subset of Professional-Edition mechanisms — not part of the Community Edition or this paper — is also the subject of a pending Chinese invention patent (application no. 202610712171X). The paper, the review, and all the evidence in it, concern only the open-source Community Edition.
>
> AI usage is disclosed in the paper's "AI usage disclosure" section.

> ⚠️ Note for any future re-submission elsewhere: the "no portion ... planned for another peer-reviewed venue" line was true at JOSS submission time. After this rejection, submitting the *same software paper* to another venue (SoftwareX/JORS/pyOpenSci) is fine — JOSS rejection releases it — but update that disclosure wording to reflect the JOSS attempt.

## 2. Why rejected — scope + significance, NOT quality

Katz was explicit: *"This is not a comment on the quality of the software or your work, just on its fit to JOSS's scope requirements."* Two prongs:

**(a) "Private development followed by public release."** JOSS requires **≥6 months of *open* development history** — public issues, PRs, releases, ideally external/cross-org contributors — not just calendar age. The editorialbot repo-analysis surfaced exactly the disfavored pattern:
- **356 / 356 commits by one author**; community signal near-zero: **1 star, 2 forks, 1 non-author commenter, 8 issues, 5 PRs**.
- Code arrived in concentrated 48-hour bursts: **Nov 11–13 2025 = 36.1%** of all code (first two days), **Jun 16–18 2026 = 13.5%** (the v0.5 Pro mechanisms held back for patent novelty, released only after the 06-17 初审合格 gate), **Apr 20–22 = 10.2%**.
- The paper claimed ~7.4 months public history clears the 6-month gate — true on the calendar, but the *shape* of that history (one author, big private-then-pushed dumps, no external engagement) is what the editor read as private development.

**(b) No *demonstrated* reuse.** Katz quoted the paper's line — *"The software is ready for that reuse and the evidence is concrete rather than aspirational"* — and said it **does not show the third-party reuse JOSS looks for**. The only real-world use cited (the cardiovascular CAC pipeline) is the author's own team, not independent adopters.

**Not reasons** (do not chase these): License "Other" flag (dual-license `LICENSE-NOTICE.md` confused the classifier; core is clean Apache-2.0) and the 3 no-DOI references — both green/minor.

## 3. Consequence

Desk-reject = issue closed, cannot re-open or re-submit the same issue. JOSS pointed to [other venues](https://joss.readthedocs.io/en/latest/submitting.html#other-venues-for-reviewing-and-publishing-software-packages). A future JOSS attempt would need *genuine* accrued open-development history (months of external issues/PRs/users), not a re-submit of the same state.

## 4. Free / low-cost venues for a citable software artifact

| Venue | Cost | What you get | Fit for pyobfus | Gate |
|---|---|---|---|---|
| **Zenodo** (GitHub release archive) | Free | Crossref/DataCite **DOI**, citable, versioned | ✅ Immediate, zero gate — pyobfus can get a DOI this week | None (just connect repo + tag a release) |
| **arXiv** cs.SE / cs.CR preprint | Free | Timestamped preprint, Google Scholar visibility | ✅ Good for the *research/benchmark* paper (P2-18), not the software-description one | Endorsement may be needed for first cs submission |
| **pyOpenSci** | Free | Community peer review of Python packages; partners with JOSS | ⚠️ Similar open-dev/community expectations as JOSS — same risk unless adoption grows | Scope review; volunteer-driven |
| **JOSS (re-try later)** | Free | Peer-reviewed Crossref DOI | ⚠️ Only after real open-dev history accrues | The 6-month *open* history + reuse bar that just rejected it |
| **JORS** (Journal of Open Research Software, Ubiquity) | **APC ~£300–500** | Indexed OA software metapaper | ⚠️ Less strict on community than JOSS, but not free | Editorial review |
| **SoftwareX** (Elsevier) | **APC ~€2,500** | SCIE-indexed (IF ~3), software metapaper | Possible if an indexed journal matters | Editorial + review; do NOT dual-submit a JOSS paper here |

**Recommendation (free path):** Zenodo DOI now (instant, unconditional, gives a real citation handle) + keep developing in the open so a later JOSS or pyOpenSci attempt can show genuine community history. Reserve SoftwareX/JORS only if an *indexed* journal credential is specifically needed.

> ✅ **DONE 2026-06-25 — Zenodo DOI minted.** GitHub→Zenodo integration enabled; archived via the `zenodo-archive-v0.5.2` release (tagged outside `v*.*.*` so it did not trigger the PyPI publish workflow). **Concept DOI (cite this, all versions): `10.5281/zenodo.20846053`** · version DOI (this snapshot): `10.5281/zenodo.20846054`. Wired into `CITATION.cff` (`doi:`) and the README DOI badge. Record confirmed on the Zenodo page (ORCID linked, Apache-2.0, keywords, "Cite all versions" = concept DOI).
>
> **Operational notes for future sessions:**
> - **MCP needs no separate Zenodo record.** `pyobfus-mcp` lives in this same repo (`pyobfus_mcp/`), so the archived zipball already contains it; the one concept DOI covers core + MCP. Cite the same DOI for both.
> - **The integration auto-archives ANY future release on this repo** — including `mcp-v*.*.*` tags — each as a new version under the same concept DOI. So core and MCP releases share one Zenodo version line (harmless for citation; the concept DOI represents the whole repo). Be selective with releases if you don't want every MCP patch to mint a Zenodo version.
> - **Version label self-corrects — don't chase it.** The bootstrap record's Version field shows the tag `zenodo-archive-v0.5.2` (ugly in the APA citation). It need NOT be fixed: the concept DOI always resolves to the *latest* version, so the next normal release (`v0.5.3`) will archive as a clean version and become what the concept DOI shows. Only edit manually (Zenodo → My dashboard → Uploads → open record → orange **Edit** button top-right → Version → `v0.5.2` → Save → Publish; DOI unchanged) if a clean citation is needed *today* (e.g. for a CV). The zip filename stays tag-derived regardless.

## 5. Strategic note — open-core / patent tension surfaced

The 06-17 patent gate (holding the v0.5 Pro mechanisms private until 初审合格, then releasing in one burst) is part of what produced the "private-then-public" commit shape JOSS rejected. The IP-protection strategy and the open-development credibility JOSS wants are in genuine tension; any future academic-credit path has to account for that, or route credit through a venue (Zenodo/arXiv) that does not gate on community-development optics.

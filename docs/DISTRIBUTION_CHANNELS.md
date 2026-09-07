# Distribution Channels State

Living reference of where `pyobfus` has a foothold, what each account looks like, and what's pending. Updated when a channel's state changes.

For the **why** behind the channel mix, see [AI_INTEGRATION_STRATEGY.md](AI_INTEGRATION_STRATEGY.md).
For **historical deltas** per session, see [V0.4_EXECUTION_LOG.md](V0.4_EXECUTION_LOG.md).
For the frozen post-release evidence and recheck checklist from 2026-08-24, see
[EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md](EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md).

**Last updated**: 2026-09-07 (**Open VSX is LIVE** — `zhurong2020.pyobfus`
v0.4.2, independently re-checked at HTTP 200 on both the extension page and the
API after the immediate post-upload 404 turned out to be index propagation lag.
**Glama**: frank@glama.ai followed up with "Build errors should be fixed now";
the duplicate-listing / badge-URL question is still unanswered and no build has
been retried on our side yet. Earlier the same day: distribution expansion
research recorded. pyobfus 0.5.22 published through OIDC — Python
3.14 remote-debug hardening advisory in `--check`; PyPI `latest=0.5.22`, both
Integrity provenance endpoints HTTP 200, GitHub Release created, and the
advisory verified against a fresh install. vscode-extension 0.4.2 published in
the same round — a Security fix containing "Generate pyobfus.yaml" writes to the
workspace; tag, GitHub Release with the vsix, and the maintainer's manual
Marketplace upload are all done, with the public listing independently
re-checked as `"version":"0.4.2"`. **pyobfus-mcp 0.3.11 released** — the hold
was lifted once a real defect joined the pending metadata fix: the initialize
handshake was advertising the mcp SDK's version rather than the package's.
Glama's Build steps still need a manual bump to 0.3.11.)

> **Note (2026-05-09)**: most of the per-channel facts below are now current as of Session 23. Outside of the launch wave (HN 5-11 / Reddit 5-12 / CN trio 5-8/9), the live state is reflected here. Consult `docs/POST_V0.4_TODO.md` for forward TODO and `docs/V0.4_EXECUTION_LOG.md` for session-by-session deltas.

---

## 🟢 Live and owned

### PyPI — `pyobfus`
- URL: https://pypi.org/project/pyobfus/
- Current version: **0.5.22** (released 2026-09-06) · ships with PEP 740 attestations via OIDC trusted publishing
- Current headline: discovery-focused metadata and README/FAQ improvements around pre-shipping protection, reverse mapping, provenance, and AI-assisted debugging; runtime behavior unchanged.
- Prior headline (0.5.19): `--dry-run --json` emits a versioned `plan` object (effective config, selected/excluded files with reasons, artifacts tagged ship/retain-internal/optional; relative labels only, not applyable); opt-in `--verify-syntax` compiles generated output in memory post-build (no import/execute, no `__pycache__`) and reports `syntax_valid` with no runtime-correctness claim.
- Prior headline (0.5.18): config-aware `--check` reports the effective project configuration and findings already mitigated by it, while preserving high-risk findings and exit-code semantics.
- Pre-v0.4 baseline: ~324 downloads / month, ~30% real users (rest is mirror noise)
- 2026-08-24 pypistats snapshot (data through 08-23, known mirrors excluded):
  day/week/month `27 / 502 / 2,059`. Weekly growth is dominated by release-day
  spikes (08-17 `124`, 08-20 `119`, 08-22 `151`); 08-23 returned to `27`, so
  this is not yet evidence of a higher organic baseline.
- 2026-08-26 recheck (data through 08-25): 08-24 release-day downloads were
  `137`, then returned to `27` on 08-25; latest day/week/month is
  `27 / 512 / 2,178`. No organic-baseline uplift established.
- 2026-09-02 recheck (data through 08-31): latest day/week/month is
  `31 / 376 / 2,338`; non-release days average `26.4`, median `27`, unchanged
  from the quiet baseline. Data does not yet include the 09-01 release.
- Tracker: `gh api repos/zhurong2020/pyobfus` + PePy

### PyPI — `pyobfus-mcp`
- URL: https://pypi.org/project/pyobfus-mcp/
- Current version: **0.3.12** (released 2026-09-07) · ships with PEP 740 attestations via OIDC trusted publishing
- 0.3.12 contents: fixes a startup-crash regression introduced hours earlier in
  0.3.11. That release resolved its version through a module-level
  `from pyobfus_mcp import __version__`, which raises `ImportError` when the cwd
  holds a `pyobfus_mcp/` directory with no `__init__.py` — the two merge into a
  namespace package and `__init__.py` never runs. **Impact was
  development-scoped, measured not assumed**: a regular `pip install` is fine
  even from a shadowing cwd (the site-packages package outranks the namespace
  portion — verified against 0.3.11 and 0.3.12 side by side); the crash needs
  an *editable* install, whose `__editable__` finder resolves submodules while
  the directory captures the top-level name. That is the CI smoke job's layout,
  which is what caught it. Version lookup is now fully guarded and falls through to
  skipping the stamp. Same-day release despite the 1-2 day spacing rule, on the
  precedent of vscode-extension 0.2.1: a genuine crash fix jumps the gate.
- 0.3.11 contents: two fixes, no schema change. (1) The `initialize` handshake
  advertised the mcp SDK's version instead of this package's, so clients saw a
  version pyobfus-mcp never had — found in a Glama build's instance logs. (2)
  Replaced the retired `modelcontextprotocol/servers` directory URL in package
  metadata with the live Registry endpoint. Released once (1) gave the version
  real content; the metadata fix alone had not justified the manual Glama
  Build-steps bump each MCP release costs.
- 0.3.10 contents: intent-oriented Registry description and expanded PyPI discovery keywords; tool behavior and schemas unchanged.
- 0.3.9 contents: `check_obfuscation_risks` adds default-on `use_project_config`, returns effective-config and excluded-finding context from Core, and moves the runtime dependency floor to `pyobfus>=0.5.18`.
- 2026-08-24 pypistats snapshot (data through 08-23, known mirrors excluded):
  day/week/month `11 / 242 / 772`. Release-day spikes (08-17 `95`, 08-22 `110`)
  dominate the weekly increase; 08-23 returned to `11`. CI/CD traffic remains
  included, so do not treat the increase as organic adoption yet.
- 2026-08-26 recheck (data through 08-25): 08-24 release-day downloads were
  `99`, then returned to `8` on 08-25; latest day/week/month is
  `8 / 245 / 874`. No organic-baseline uplift established.
- 2026-09-02 recheck (data through 08-31): latest day/week/month is
  `6 / 232 / 1,090`; non-release days average `13.5`, median `12`. The slight
  rise is too short and release-adjacent to classify as organic growth.

### GitHub — `zhurong2020/pyobfus`
- URL: https://github.com/zhurong2020/pyobfus
- Visibility: public
- Stars: 6 (2026-08-24 snapshot; historical v0.4 target was 100+)
- Topics (19, updated 2026-09-01): includes `python-obfuscator`, `ast-obfuscation`, `mcp-server`, `reverse-mapping`, `stack-trace-deobfuscation`, `debuggable-obfuscation`, `github-copilot`, `codebuddy`, `provenance`, and `apache-2-0` discovery surfaces.
- 2026-08-24 feedback snapshot: 6 stars, 2 forks, 0 open issues/PRs; six
  Discussions with no new external comment on the 0.5.x announcement or
  dependency advisory. 14-day Traffic: 155 views / 65 unique visitors and
  1,480 clones / 158 unique cloners. Release-day automation dominates clones;
  08-23 nevertheless recorded 10 unique cloners. Treat as interest, not proven
  retention or production adoption.
- 2026-08-26 feedback recheck: still 6 stars, 2 forks and no open issue/PR or
  new Discussion comment. 14-day Traffic is now 176 views / 72 unique and
  1,751 clones / 182 unique. Release day 08-24 produced 268 clones / 31 unique;
  08-25 returned to 10 / 6. README and CHANGELOG each had only 3 unique views,
  so there is still no attributable `dependency_advisory` usage signal.
- 2026-09-02 feedback recheck: 14-day traffic is 1,999 clones / 202 unique and
  214 views / 85 unique. Clone spikes remain release-aligned (08-28: 188/28;
  08-30: 414/29), followed by 08-29 `5/3` and 08-31 `20/9` quiet-day levels.
  Still 6 stars, 2 forks, 0 open issue/PR, and no new Discussion reply.

### VS Code Marketplace — `zhurong2020.pyobfus`
- Current published version: **0.4.2** (2026-09-06). The same VSIX is now also
  on Open VSX — see the dedicated section below.
- 2026-08-24 public Gallery API: version 0.4.1, 3 installs, 124 downloads.
- No identifiable user rating/review signal yet; the API's weighted-rating
  prior is not evidence of an actual review. Continue tracking installs and
  real reviews, not raw update/download count alone.
- Wiki: disabled · Discussions: enabled · Issues: open
- Releases: latest `v0.5.20` and `mcp-v0.3.10` (2026-09-01), plus earlier Core, MCP, and VS Code tags (MCP releases attach wheel+sdist).

### Open VSX — `zhurong2020.pyobfus` 🟢 LIVE
- Public page: https://open-vsx.org/extension/zhurong2020/pyobfus
- API: https://open-vsx.org/api/zhurong2020/pyobfus
- **Published 2026-09-07**, version **0.4.2** (same VSIX as the Marketplace
  release, so the two registries are in sync). `ovsx` returned
  `Published zhurong2020.pyobfus v0.4.2`.
- **Independently re-checked 2026-09-07**: both URLs HTTP 200; API reports
  `version=0.4.2`, `license=Apache-2.0`, `timestamp=2026-09-07T00:59:01Z`,
  `allVersions=[latest, 0.4.2]`, `downloadCount=0`, `reviewCount=0`. The
  maintainer's browser view matches (Versions table `0.4.2 / Universal`,
  1-1 of 1).
- The immediate post-upload "Extension not found" from the CLI/API was **index
  propagation lag**, not a failed publish; it resolved on its own the same day.
  Record the lag, do not conclude failure from a first 404.
- `verified: false` in the API is Open VSX's **namespace ownership** flag, not
  a publish or content-review verdict — public namespaces default to false.
  Not a defect, and not something to chase unless we want the ownership badge.
- `downloadCount=0` is the day-one baseline; look for real installs at the next
  periodic channel recheck rather than reading zero as a problem.
- Publish credential: Vaultwarden entry `Open VSX Access Token (pyobfus)`
  (folder `Publishing`). Sole copy — no local dotfile cache, never in the repo
  or CI. Rotated periodically by the maintainer; a rotation only changes that
  entry's password. Re-publish runbook and usage:
  [OPEN_VSX_PUBLISH_PLAN.md](OPEN_VSX_PUBLISH_PLAN.md).
- Why this channel: reaches VSCodium / Gitpod / Eclipse Theia / code-server
  users who cannot install from the Microsoft Marketplace.

### 有心工坊 (personal blog)
- URL: https://www.arong.eu.org
- Content: CN-primary, cross-links to pyobfus in tech-empowerment (技术赋能) category
- Role in channel mix: long-form canonical CN article host; dev.to posts link here for the CN version

### Stack Overflow — Rong Zhu
- URL: https://stackoverflow.com/users/... (11 rep · 4 bronze badges)
- **Status: ⏸️ SEEDING PAUSED** (see `_drafts/stackoverflow-seeding-targets.md`)
- Rationale: SO's site-wide AI-content ban + low per-question traffic + low-rep account = bad risk/reward
- Re-evaluation trigger: pyobfus stars > 300 OR 6 months elapsed (whichever first)

### dev.to — `@zhurong2020` 🟢 FIRST POST LIVE
- URL: https://dev.to/zhurong2020
- Created: 2026-04-22
- Profile: Rong Zhu · `#f59e08` brand color · bio + 4 "Coding" fields + Work + Pronouns filled
- Current metrics (start of 2026-05-07 evening · post-publish baseline):
  - **Posts: 1** · Comments: 0 · Followers: 0
  - Following users: 28 (dev.to auto-suggestions from signup flow)
  - Following tags: 6
- Warm-up plan (executed pre-launch):
  - [x] Follow 10-15 deliberately-chosen MCP / python-obfuscation / claude-code authors
  - [x] Leave 3-5 substantive comments on related posts
  - [x] Post #1 scheduled 2026-04-24 evening → slipped to **2026-05-07 evening** (article went through v1 → v2 → v3 voice rewrite → v4 GPTZero-diagnostic-driven rewrite before final publish)
- **First post (LIVE 2026-05-07)**: *"Let Claude Code Debug Your Obfuscated Python: A Guide to the pyobfus MCP Integration"*
  - URL: <https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm>
  - Source-of-truth file: `_drafts/article-01-claude-code-mcp-integration.md` (kept post-publish for revision history)
  - Tags: `ai`, `python`, `claudecode`, `mcp`
  - Cover: `pyobfus-legal/software_copyright/screenshots/03_obfuscate_demo.png` (BEFORE/AFTER side-by-side)
  - 2 inline images: `04_json_output.png` (after Preflight check section) + `03_obfuscate_demo.png` (after Obfuscate-with-mapping section)
  - Body: 1,603 prose words · 9 fenced code blocks · disclosure line up-front

#### Auto-followed users after signup (2026-04-22)
Recording for provenance — these are dev.to's recommendations, not deliberate picks. Curated follow-ups happen during warm-up.

euromoscow · kevinmel2000 · bnlucas · hejhdiss · whoffagents · andreap · saqibjamil7866 · prashant_patil_9e62d3fa8a · luckypipewrench · shatru123 · andreas_eckhoff_7592e9859 · yaniv2809 · dev_rajput_2d46f92f8a3418 · idevusefulstuff · jon_at_backboardio · the_nortern_dev · elshadhu · bhavna_b_baa952ae51dac930 · marcosomma · syedahmershah · konark_13 · webdeveloperhyper · chocoscoding · codewithshahan · eayurt · code42cate · crd · jess

Note: `@jess` is Jess Lee, dev.to co-founder — useful to keep; `@code42cate` (Jonas Scholz) is a dev-tools creator — relevant to follow deliberately.

---

### MCP Registry — `io.github.zhurong2020/pyobfus-mcp` 🟢 LIVE
- URL: https://registry.modelcontextprotocol.io/v0/servers?search=pyobfus
- **0.3.11 published 2026-09-07, independently confirmed**: the versions
  endpoint reports `0.3.11` `active` / `isLatest=true`, published
  `2026-09-07T06:10:07Z`. Published manually with `mcp-publisher` — the release
  workflow covers PyPI only, it has **no** Registry step, so a Registry
  publication never happens automatically on a tag.
  - Retrieval note: immediately after publishing, the `?search=pyobfus`
    endpoint still returned 0.3.10 as `isLatest` and did not list 0.3.11 at
    all; the `/v0/servers/<name>/versions` endpoint already had it. The search
    index caught up on a re-query minutes later. Same failure-to-conclude trap
    as Open VSX's post-upload 404 — **query the versions endpoint, and never
    read a stale search index as a failed publish.**
  - Auth: the cached `~/.config/mcp-publisher/token.json` JWT is short-lived
    (~80 min), so a re-login is needed almost every time. Non-interactive path
    works: `mcp-publisher login github --token "$(gh auth token)"` (note the
    modern `--token` spelling; the older docs show `-token`).
  - The publisher-claimed `_meta.io.github.zhurong2020.pyobfus_mcp` namespace
    is still stripped server-side, unchanged since 0.2.0.
- Latest previously confirmed: **0.3.10** (2026-09-02 Registry publication;
  package released 2026-09-01) · status: `active` · `isLatest=true`. The public
  version endpoint also confirms package version 0.3.10 and the updated
  pre-shipping / reverse-traceback / no-phone-home description. The prior
  TLS/EOF outage is resolved; no rebuild, retag, or PyPI re-upload was needed.
- 0.3.10 contents: discovery metadata and Registry intent-description updates;
  runtime behavior and schemas are unchanged. Prior 0.3.9 added default-on
  project-config awareness and runtime floor `pyobfus>=0.5.18`. Previous 0.3.6
  hardening: `pyobfus_mcp/server.json` validates against the official
  `2025-12-11` schema and includes GitHub repository stable ID `1093960892`;
  `fileSha256` remains omitted because the PyPI wheel/sdist multi-artifact model
  makes a single optional hash ambiguous.
- Implications: Claude Desktop / Claude Code / Cursor / Windsurf / Zed users querying the registry for "pyobfus" or "python obfuscator" will discover this server without manual config file edits.

### Glama — `zhurong2020/pyobfus` 🟢 LISTED AND HEALTHY (resubmission is NOT needed)
- Public page: https://glama.ai/mcp/servers/zhurong2020/pyobfus
- 2026-08-21 recheck: the public page is reachable and still exposes 8 tool names, but its version metadata is stale (shows v0.5.13; current is 0.5.16); the older API path `/api/mcp/v1/servers/io.github.zhurong2020/pyobfus-mcp` still returns `not_found`.
- 2026-08-20: third-party maintainers independently reproduced both symptoms (build stuck on `debian:trixie-slim`, page OK but public API stale) — confirms this is Glama-side infra/sync, not a pyobfus-mcp code issue. Discord `#support` still unanswered as of 08-21; policy is passive-wait, no code change, no re-pin until Glama responds.
- 2026-08-22 recheck (post 0.5.16 release, user-supplied page dump): "Recent Releases" panel now lists **`0.5.12` dated 2026-08-22** — that version number belongs to the core `pyobfus` package's last GitHub Release (tagged 2026-08-06, before this session added `v0.5.16`), not to `pyobfus-mcp`'s own 0.3.x scheme, so Glama appears to be pulling GitHub Release tags from the shared `zhurong2020/pyobfus` repo without filtering by which sub-package they belong to, and mislabeling the date on top of that. Configured "Pinned commit SHA" also still reads `cd823d1` (pre-dates the 0.5.16 release commit `f694f3a`). Same underlying Glama-side crawler defect as above — no action taken, policy unchanged.
- 2026-08-24 post-0.3.8 recheck (user-supplied admin page): Build steps has already
  updated correctly to `pyobfus-mcp==0.3.8` and triggered Recent Test
  `01a033e4-3336-7e7b-9792-0d7e056d2dba` at 21:09. The page excerpt does not
  expose that test's pass/fail result, so record it only as "triggered", not
  "successful". Glama's newly advertised API path
  `/api/mcp/v1/servers/zhurong2020/pyobfus` is reachable but still returns
  `tools: []`. "Recent Releases" now calls the same event `0.5.14`, again proving
  that panel's numbering is not the MCP package's real 0.3.x version. Pinned SHA
  is now `e44e687` while repository HEAD is `8f00fba`; this does not change the
  runtime package because the Dockerfile explicitly installs the PyPI 0.3.8
  artifact, but it does explain stale checkout/page metadata. No local code fix.
- 2026-08-24 final test evidence (user-supplied admin logs): test
  `01a033e4-3336-7e7b-9792-0d7e056d2dba` completed **success** in 12.1s.
  Install logs confirm `pyobfus-mcp==0.3.8` plus `pyobfus==0.5.17`; the live
  `ListToolsRequest` returned all 8 tools and the new
  `verify_dependencies_online` input field. This closes the build/runtime side
  completely. The public API's `tools: []` is now proven to be directory sync
  drift, not a server introspection failure. Build Spec reports
  `pinnedCommit: null` even though generated clone logs still checkout
  `e44e687`, another Glama metadata inconsistency with no runtime impact.
- 2026-08-26 programmatic recheck: the public listing still exposes all 8 tool
  names. The formerly public API path now returns HTTP 401, so it is no longer a
  usable unauthenticated health check; continue treating the listing plus the
  successful live `ListToolsRequest` as the available evidence.
- 2026-09-05 (email from frank@glama.ai, replying to the 2026-05-03 rejection)
  — ⚠️ **superseded 2026-09-07: its premise was falsified and the resubmission
  it asks for must NOT be done; see the 09-07 entries at the end of this
  section before acting on anything below**:
  the original submission was **rejected and never approved**, so there is no
  listing to re-review; the instruction is to resubmit through the normal
  submission flow now that the README, `glama.yaml` and the Dockerfile are in
  place. This supersedes the "directory sync drift" reading recorded above — the
  public API record most likely stayed empty because the entry never entered the
  approved directory, even though the server page renders and builds run. Note
  the tension: `https://glama.ai/mcp/servers/zhurong2020/pyobfus` is live and
  current (all 8 tools, a quality grade, references v0.5.21), so Frank may be
  answering from the May ticket rather than the present page state. Open question
  put to him: whether resubmitting duplicates the entry or moves the URL, which
  would break the Glama score badge carried in the root README.
- 2026-09-06 build evidence: the admin **Build steps** field does *not* follow new
  releases — it sat at `pyobfus-mcp==0.3.8` through 0.3.9 and 0.3.10 until the
  maintainer bumped it manually to `0.3.10`. Builds still fail before any build
  step executes: `01a06fa7-39aa-70ed-8186-b98260d7eb24` (2026-09-05, 7 min,
  `failed to resolve source metadata for docker.io/library/debian:trixie-slim …
  context deadline exceeded`); `01a074ae-6150-7ce8-b2cf-e20ce70b7361` (2026-09-06,
  1m38s, same metadata timeout, and Glama's own error text now reads "The Glama
  builder lost its BuildKit session before any build step ran. This is a
  platform-side fault, not a problem with your build spec, base image or
  repository"); and the manual retry `01a074b6-361f-732c-adc8-e876f9c7f501`
  (2026-09-06, 2 min, `AbortError: Build aborted` raised by Glama's own build
  timeout). "Retrying usually succeeds" has not held across 08-07, 08-17, 09-05
  and two attempts on 09-06.
- 2026-09-06 correction to an earlier assumption: Glama does **not** build from
  the repository's `pyobfus_mcp/Dockerfile`. It synthesises its own Dockerfile
  from the admin Build Spec (`debian:trixie-slim` + uv + `mcp-proxy` + `git clone`
  followed by a checkout of the main tip) and then runs `buildSteps`. The repo
  Dockerfile matters for submission review only. Both stale artifacts were
  refreshed anyway in `e967754` — Dockerfile pin `0.2.0` → `0.3.10`, and
  `glama.yaml` from "Seven tools" to eight, adding `protect_project` and the
  Copilot/CodeBuddy clients. Verified by installing `pyobfus-mcp==0.3.10` into a
  clean venv and completing a real MCP `initialize` + `tools/list` handshake that
  returned all 8 tools, so server-side introspection is sound.
- 2026-09-07 (second email from frank@glama.ai, replying to the build evidence
  above): **"Build errors should be fixed now."** Glama therefore treats the
  BuildKit/base-image failures as a platform-side fault they have addressed.
  **Not verified on our side** — no build has been retried since that email, so
  record this as an upstream claim, not observed behaviour. Do not write "builds
  work again" anywhere until a real build run is seen to complete.
- 2026-09-07 open question, still unanswered: Frank did **not** address whether
  resubmitting creates a duplicate entry or moves the URL. The README score
  badge (`README.md`, the `glama.ai/mcp/servers/zhurong2020/pyobfus/badges/
  score.svg` link) is pinned to the current path, so a URL move breaks it. His
  2026-09-05 instruction to resubmit through the normal flow still stands.
- **Next action** (maintainer, manual, does not block local work), in order:
  1. Trigger a build from the Glama admin panel with Build steps already pinned
     at `pyobfus-mcp==0.3.10`, and capture the result either way.
  2. If it completes, resubmit through the normal submission flow per the
     2026-09-05 instruction.
  3. After resubmission, check whether the public URL is still
     `glama.ai/mcp/servers/zhurong2020/pyobfus`; if it moved, update the README
     badge and every link recorded in this file.
  Policy unchanged otherwise: no pyobfus-mcp code change for Glama, and MCP
  0.3.11 stays unreleased until there is substantive MCP work to ship (each
  release costs a manual Build-steps bump).
- 2026-09-07 admin panel (maintainer-supplied dump), read in three tiers of
  evidence rather than as one conclusion:
  - **Fact.** Build steps read `pyobfus-mcp==0.3.10`, so the manual bump held.
    Pinned commit SHA is now `d2f5d75` and the page reports
    `Current head commit: d2f5d75 (sync)`, so the pin is current — the first
    time it has not lagged HEAD. (Later doc commits move HEAD again; this does
    not affect the build, which installs the PyPI artifact, not the checkout.)
  - **Fact.** Recent Tests has a new entry `01a07845-bc57-7c91-905f-
    df27d33ea885`, 2026-09-07 03:50, labelled `0.5.21` — the first run after
    Frank's "build errors should be fixed now".
  - **Inference, not evidence.** The panel exposes **no pass/fail field**, the
    same limitation recorded on 2026-08-24, so this is *not* logged as a
    success. What is suggestive: the three known-failed runs (`01a06fa7`,
    `01a074ae`, `01a074b6`) carry no version label at all, while `01a07845`
    carries one, matching `01a06066`/`0.5.20` from 09-02; and "Recent
    Releases" gained a `0.5.21` dated 2026-09-07. Since that panel is Glama's
    internal counter rather than the MCP version, a fresh counter entry on the
    same date suggests the run got far enough to produce a release. Suggestive
    of recovery — still short of the status field.
  - **To confirm**: open that test's own detail/log view for an explicit
    result, as was done for `01a033e4` on 2026-08-24. Only then record the
    build side as recovered.
- 2026-09-07 **build side CONFIRMED RECOVERED** — the test detail view for
  `01a07845-bc57-7c91-905f-df27d33ea885` reports an explicit `Status: success`
  in `14s`. The inference logged above is now settled by the status field, so
  Frank's "build errors should be fixed now" is verified, not just claimed.
  Evidence from that run:
  - All five Docker stages completed through `exporting to image`. The failure
    mode of 09-05/09-06 — dying at `load metadata for debian:trixie-slim`
    before any build step — did not recur.
  - Installed `pyobfus-mcp==0.3.10` plus `pyobfus==0.5.22`, i.e. the pinned MCP
    release pulling the current core.
  - Live handshake succeeded: `initialize` returned protocol `2025-11-25`, and
    `ListToolsRequest` enumerated **all 8 tools**. `ListPromptsRequest` and
    `ListResourcesRequest` returned empty, which is correct — this server
    exposes tools only.
  - `Release Created ... Version 0.5.21, Published 2026-09-07 03:50` confirms
    the "Recent Releases" panel is generated *by builds*, which is why the
    earlier version-label pattern was a usable signal.
  - Timezone note for future readers: the log lines read `2026-09-06T19:50`
    (UTC) while the panel header reads `2026-09-07 03:50` (UTC+8). Same run,
    not two.
- 2026-09-07 two discrepancies visible in that same successful run, neither
  blocking, both worth not re-discovering later:
  - **`pinnedCommit: null` in the Build Spec while the clone log checks out
    `d2f5d75e74…`.** Identical to the 2026-08-24 observation (then `e44e687`),
    so this is a standing Glama metadata inconsistency, not a new fault. No
    runtime impact — the image installs the PyPI artifact, not the checkout.
  - **The configured Python version does not govern the install.** Admin sets
    `Python version: 3.12` and the synthesised Dockerfile runs
    `uv python install 3.12 --default`, but the install step logs
    `Using Python 3.13.5 environment at: /usr` — `uv pip install --system`
    landed the package in Debian's system Python instead. No functional impact
    observed (server started, 8 tools enumerated), but do not read that admin
    field as controlling the runtime interpreter.
- 2026-09-07 **a defect of ours, surfaced by Glama's instance logs**: the
  handshake returns `serverInfo: {name: "pyobfus", version: "1.29.1"}`, and
  `1.29.1` is the **mcp SDK version** installed in that image — not
  `pyobfus-mcp` 0.3.10, and not `pyobfus` 0.5.22. Every MCP client sees a
  version this package has never had, and it changes whenever the SDK updates.
  Root cause verified in the code, not guessed: `server.py` carries a comment
  claiming "FastMCP populates that from package metadata", which is false.
  `FastMCP(name=...)` leaves the inner low-level `Server.version` at `None`
  and the SDK then reports its own. Confirmed against the installed SDK
  (mcp 1.27.0): `FastMCP.__init__` has no `version` parameter — so the 0.1.2
  removal that fixed the startup crash was correct — while
  `mcp.server.lowlevel.Server.__init__` does. Setting
  `app._mcp_server.version = __version__` after construction makes
  `create_initialization_options().server_version` return `0.3.10`, verified
  end to end. Caveat: `_mcp_server` is private, so the fix needs a guard
  rather than a bare assignment. **Fixed and released** the same day in
  pyobfus-mcp 0.3.11, with the follow-on startup-crash regression fixed in
  0.3.12 — see the confirmation below.
- 2026-09-07 **the serverInfo fix is confirmed in production, in the very
  environment that exposed it.** After the maintainer bumped Build steps to
  `pyobfus-mcp==0.3.12`, test `01a07aa2-fd8e-7831-9088-b43ecb585f54`
  (14:51 UTC+8 / 06:51 UTC) reports `Status: success` in 14.2s, and its instance
  log now reads `serverInfo: {name: "pyobfus", version: "0.3.12"}` where it
  previously read `"1.29.1"` — with `mcp==1.29.1` still installed in that image,
  so the SDK version that was leaking is the same one present now. All 8 tools
  enumerated. The defect was found in Glama's logs and closed against Glama's
  logs, same environment, same SDK.
- 2026-09-07 build recovery is now a **pattern, not a single data point**: two
  consecutive successful builds (`01a07845` 14s, `01a07aa2` 14.2s) after five
  consecutive failures across 08-07 / 08-17 / 09-05 / 09-06 ×2.
- 2026-09-07 the two standing Glama-side quirks recurred unchanged in this run,
  now observed three times, so treat them as permanent background rather than
  investigating again: Build Spec reports `pinnedCommit: null` while the clone
  log checks out `d2f5d75`, and the install logs `Using Python 3.13.5` despite
  the admin field reading 3.12. Also note the pinned commit is now well behind
  HEAD, which remains harmless because the image installs the PyPI artifact.
  The "Release Created" panel called this build `0.5.22` — the core package's
  version, again confirming that counter tracks GitHub release tags from the
  shared repo rather than the MCP package's 0.3.x line.
- 2026-09-07 **the "never approved" premise is falsified — do NOT resubmit.**
  Checked the one thing nobody had checked: the public directory search itself.
  `https://glama.ai/mcp/servers?query=pyobfus` returns `pyobfus-mcp` under owner
  `zhurong2020` with grades **A license / A quality / A maintenance**, its
  individual tools indexed and separately graded, and **no pending /
  unapproved / under-review label of any kind**. Detail page and badge both
  HTTP 200. A record that is searchable, graded and continuously rebuilt inside
  an 83,209-server directory is a live listing, whatever the May ticket says.
  - Most likely explanation for the 2026-09-05 email: its subject line is
    `Re: Your MCP server "pyobfus-mcp" was not approved on Glama` — the
    **May** rejection thread. Frank appears to have answered from that ticket
    without re-checking the present state, which is exactly the tension already
    flagged when the mail arrived.
  - **Method lesson, worth more than the conclusion**: `/api/mcp/v1/servers/...`
    returning `not_found` and later **HTTP 401** was treated for weeks as
    evidence the entry was missing from the directory. It is not. 401 is an
    authentication failure — the endpoint now requires an API key for everyone
    — and `not_found` on a deprecated path says nothing about listing state.
    **Absence of access is not evidence of absence.** The correct probe is the
    public search page, which costs one request and was never run.
  - Consequence: resubmission is removed from the action list. It carried real
    downside (a possible duplicate entry, or a moved URL breaking the README
    score badge) in exchange for fixing a problem that does not exist.
  - Residual drift, harmless: the search card reads
    `Updated a day ago (2026-09-06 04:31 UTC)`, predating today's 0.3.12 build,
    so the card's timestamp lags the build pipeline.

### MCP Skills trust score — 🟡 ESTABLISHED / NOT VERIFIED
- 2026-08-24 official free score API scan for `zhurong2020/pyobfus`: composite
  **6.06**, tier `established`, 14 signals, `verified=false`.
- Positive evidence: `no safety findings`; the scanner detected the AI skill.
- Blocking flags: `SINGLE_AUTHOR_LOW_ADOPTION` and `low_legit`. Because Verified
  requires composite >=7.0 plus dimension floors and no disqualifiers, the repo
  cannot claim the gold badge yet.
- Decision: do not buy the $2 full report or optimize code/docs merely to game
  the score. Re-scan after genuine adoption/contributor growth; external
  contributors, stars and real usage should improve the weak dimension
  honestly.

### Canopii Trust Index — 🟡 UPSTREAM ISSUE OPEN / RESCAN PENDING
- 2026-08-24 initial page state: latest scanned version was stale at MCP v0.3.7, score
  39/100 (F), confidence 81%. Its sole high failure is a broad
  `marshal.loads(...)` match at `pyobfus_pro/runtime/opacity.py:147`.
- The evidence is in the sibling Pro runtime, not `pyobfus_mcp/`, and follows a
  successful authenticated AES-GCM decrypt. No MCP tool input reaches that
  bytes/key/plaintext path. The public Canopii rule is syntax-only and scans the
  whole monorepo, so this is not evidence of an exploitable MCP deserialization
  path.
- 2026-09-02 maintainer verification is already shown on the listing, but the
  latest scan remains stale at v0.3.9 and reports `no tools extracted` despite
  eight direct FastMCP registrations and the packaged `tool_manifest.json`.
  Upstream issue [canopii-cli#6](https://github.com/canopii-dev/canopii-cli/issues/6)
  now requests a v0.3.10 artifact/subfolder-scoped rescan and extractor fix.
- Before filing, two useful repository-wide advisories were fixed independently:
  VS Code generated-config workspace containment (`dd91387`) and the draft
  Worker WordPress credential-target restriction (`450718c`). Those sibling
  fixes do not make their paths part of the installable MCP package.
- Follow-up acceptance criteria: latest version >=0.3.10, eight tools extracted,
  sibling components excluded from MCP evidence, and PyPI provenance evaluated.
  Check issue replies during external-status reviews; follow up once after 14
  days if silent. Do not embed the F badge or change product behavior merely to
  silence the scanner.
- Full evidence and the exact recheck sequence:
  [EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md](EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md).

### Claude Plugin Marketplace 🟡 PENDING
- Console entry: `pyobfus`
- 2026-08-24 maintainer recheck: still `Submitted and pending review`, submission date Aug 2.
- 2026-09-07 maintainer recheck (console dump): unchanged — still `Submitted and pending review`, still dated Aug 2, now **36 days** in queue with no state transition and no request for changes. Nothing actionable; keep the passive-wait policy and re-check on the next periodic sweep.
- Known copy issue: submitted description says `protected_project`; correct tool name is `protect_project`. Do not resubmit only for this typo; fix opportunistically if Anthropic exposes an edit/request-changes path.

### OpenSSF Best Practices passing badge 🟢 LIVE
- URL: https://www.bestpractices.dev/projects/12788
- Project ID: 12788 · achieved: 2026-05-09 04:23:38 UTC · tier: passing (Metal series) · 67/67 criteria
- Categories met: Basics 13/13 · Change Control 9/9 · Reporting 8/8 · Quality 13/13 · Security 16/16 · Analysis 8/8
- Same tier as Kubernetes / Curl / etcd
- Badge embedded in pyobfus README header (commit `eb634ab`)
- Implications: marketable third-party project-maturity credential. Cross-referenced in awesome-mcp-servers PR #5777 description (silent edit 2026-05-09). Useful in HN/Reddit launch posts as supporting evidence; useful in 软著 / patent applications as "production use" proof (see `memory/patent_software_copyright_sync_2026-05-09.md`).

## 🟡 Pending action

### `awesome-mcp-servers` community lists — 2 LIVE / 1 dead-end (refreshed 2026-06-08)
- 🟢 **`wong2/awesome-mcp-servers` LIVE** via mcpservers.org (the list has retired direct PRs; submissions go through the form-driven `mcpservers.org/submit` channel). Listing: <https://mcpservers.org/servers/zhurong2020/pyobfus>. Approval landed same-day (2026-05-08) vs the 7-day SLA.
- 🟢 **`punkpeye/awesome-mcp-servers` PR #5777 MERGED 2026-06-06** (opened 2026-05-03 · merged by punkpeye/Frank Fiegel after ~34 days at 86K★-repo human cadence). pyobfus-mcp now listed under Developer Tools. All bot gates were green throughout (`has-emoji`/`has-glama`/`valid-name`).
- ❌ **`appcypher/awesome-mcp-servers` DEAD-END** — repo owner has disabled both PRs and Issues (`gh api repos/appcypher/awesome-mcp-servers --jq '.has_issues'` returns `false`). The CONTRIBUTING.md is stale; repo is in read-only museum mode despite still appearing active. Fork retained at `zhurong2020/awesome-mcp-servers-appcypher` for re-fork in 1 click if owner reopens.
- Implications: **2 of 3 lists now actively distribute pyobfus-mcp (≥ 90K combined stars), both LIVE** (no longer PR-gated). The launch wave's awesome-list discoverability is fully in place.

---

## 🔵 Planned, not established

### Hacker News
- No account yet (if needed, use email `zhurong0525@gmail.com`)
- Intended use: **one** Show HN after dev.to article #1 gets social proof (goal: 100+ reactions on dev.to first)
- AI policy: banned outright; post must be manually written by maintainer

### Reddit — `/r/Python`
- No pyobfus-dedicated handle planned; personal account used with disclosure
- Target: **"Showcase Saturday" pinned thread** (not a standalone post)
- AI policy: mods remove AI-looking content on sight; human voice required

### Medium
- Deferred. dev.to-first; Medium considered only if dev.to article performs (>5k views) as a reach extension with AI-disclosure header

### Zhihu (知乎) / 微信公众号 / 小红书
- Not in current plan; 有心工坊 covers the CN long-form need. Revisit Q3 2026 if CN traffic signal justifies.

---

## 📊 Metrics targets (from AI_INTEGRATION_STRATEGY.md §5)

| Metric | Baseline 2026-04-22 | v0.4 target (6 weeks) | v0.5 target |
|---|---|---|---|
| PyPI `pyobfus` monthly downloads | 324 | 1,500+ | 5,000+ |
| GitHub stars | 0 | 100+ | 300+ |
| External GitHub issues opened | 0 | 1+ | 5+ |
| MCP server installs | — | 500+ | — |
| AI-assistant recommend rate (blind test) | 0/10 | 3/10 | 7/10 |
| dev.to followers | 0 (2026-04-22) → 0 (2026-05-07 post-publish) | 50+ | 200+ |
| dev.to first-post reactions @ 24h | TBD (publish 2026-05-07 evening) | 30+ | — |
| dev.to first-post reactions @ 7d | TBD | 100+ | — |
| First pyobfus Pro license sale | — | 1 | — |

Tracking cadence: every 2 weeks append a row to V0.4_EXECUTION_LOG.md.

---

## 🔁 When to update this file

Update whenever:
- A new channel is established (account created, repo forked, etc.)
- A channel's status changes (paused ↔ active)
- A publish / post goes live (note the URL + date)
- Monthly metrics snapshot (copy current row of numbers)

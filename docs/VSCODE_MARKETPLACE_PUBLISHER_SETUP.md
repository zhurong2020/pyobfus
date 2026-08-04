# VS Code Marketplace publisher setup — runbook + troubleshooting log

**Context**: getting the `pyobfus` VS Code extension (`vscode-extension/`,
see `docs/VSCODE_EXTENSION_PLAN.md`) live on the Marketplace for the first
time, 2026-08-04. The standard documented path (CLI `vsce publish` with a
PAT) turned out to be blocked by an unresolved Azure DevOps bug; this
records exactly what was tried, in what order, and the workaround that
actually worked — so a future session doesn't have to rediscover any of
this, and has a starting point if the Azure DevOps issue is ever worth
retrying (e.g. before M4's CI auto-publish work).

**Outcome**: publisher `zhurong2020` is live; `pyobfus` v0.1.0 published
successfully via the manual `.vsix` web-upload path (not `vsce publish`).
Confirmed via the Marketplace listing itself and a
"[Succeeded] Extension publish on Visual Studio Marketplace" email from
Microsoft.

## Step 1 — Create the Marketplace publisher account (worked, no issues)

1. Went to the official VS Code ["Publishing Extensions"](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) docs page.
2. Signed in at `https://marketplace.visualstudio.com` with `wuxiami@hotmail.com`.
3. Filled in the "Create Publisher" form — publisher ID `zhurong2020`, matching
   the existing brand identity used everywhere else (PyPI `zhurong2020`,
   GitHub `zhurong2020`, MCP Registry `io.github.zhurong2020`).
4. Landed on the "It's lonely here!" Manage Publishers & Extensions page —
   this confirms the **publisher account itself was created successfully**.
   This step was never the problem; everything that follows is about the
   separate "how do I actually push a build" step.

## Step 2 — CLI `vsce publish` needs a PAT, which needs an Azure DevOps org (blocked)

The documented CLI path is: create an Azure DevOps organization → generate a
Personal Access Token scoped to "Marketplace (Manage)" → `vsce publish -p
$PAT`. Azure DevOps org creation is where this got stuck.

### What was tried, in order

1. Went through the Azure DevOps get-started flow (`dev.azure.com` → sign in
   → consent screen → "Almost done... Select an Azure subscription for
   billing"). Tried this with **two different sign-ins**:
   - `wuxiami@hotmail.com` (personal account)
   - `zhurong@7fp1fj.onmicrosoft.com` (M365 Developer Program E5 sandbox
     tenant — linked/connected to the hotmail account; the actual paid
     subscription lives here)

   Both failed at the same step with: **"We couldn't find any subscriptions
   associated with this account."**

2. Independently confirmed real, valid subscriptions exist by logging into
   `portal.azure.com` with `wuxiami@hotmail.com` directly. Two subscriptions
   were listed, both eligible on paper:

   | Subscription | ID | Directory | Role | Type |
   |---|---|---|---|---|
   | zhurong free subs | `4bada6e0-463e-4b96-84fc-f9b6debb12f1` | Default Directory (wuxiamihotmail.onmicrosoft.com) | Owner | Azure Plan |
   | Azure 订阅 1 | `7d51f0c4-a972-4e5e-9390-ce245b42afde` | Default Directory (wuxiamihotmail.onmicrosoft.com) | Owner | Azure Plan |

   Both are Owner-role, Azure Plan type, same directory as the sign-in used
   in step 1 — on paper, exactly what Azure DevOps org creation should
   accept.

3. **Attempted fix #1** — switched directory using the account/directory
   picker built into the Azure DevOps org-creation flow itself. Did not
   resolve the error.

4. **Attempted fix #2** (more thorough, research-backed) — this is a
   documented, different failure mode: a *stale cross-tenant authentication
   token*, fixed by forcing a genuine re-authentication via
   **Azure Portal's own "Directories + subscriptions" blade → "Switch"**
   (not the org-creation flow's own picker, which doesn't force a full
   re-auth). Tried this too. Still failed with the same "no subscriptions
   found" error afterward.

### Conclusion on root cause

Not definitively identified. Two candidate explanations, neither confirmed:
- M365 Developer Program (E5 sandbox) subscriptions may simply not be
  recognized as valid Azure DevOps org-creation billing anchors — a
  documented category of limitation, distinct from the stale-token failure
  mode that fix #2 targets (and which was ruled out here, since fix #2
  didn't help).
- An unrelated, currently-unresolved product-side bug in the Azure DevOps
  org-creation flow.

**Not worth further time sinking into for now** — the workaround below
fully unblocks publishing. Worth a periodic retry (e.g. next time a PAT is
needed for M4's CI auto-publish work), since this may simply resolve itself
on Microsoft's side.

## Step 3 — Workaround: manual `.vsix` upload via the Marketplace web UI (worked)

Key realization: `vsce package` (building the `.vsix` file) never touches
Azure DevOps or a PAT — only `vsce publish` (the CLI *upload* command) does.
The Marketplace web UI has its own **independent** upload path that uses the
browser's own login session, never touching Azure DevOps/PAT machinery at
all.

1. Built a clean, production `.vsix` locally (no PAT needed):
   ```bash
   cd vscode-extension
   npx vsce package --no-dependencies
   ```
   Produced `pyobfus-0.1.0.vsix` (8 files, ~32 KB: `LICENSE.txt`,
   `changelog.md`, `icon.png`, `package.json`, `readme.md`,
   `dist/extension.js` — a clean package, no dev artifacts, confirming
   `.vscodeignore` is correctly scoped).
2. Went to `https://marketplace.visualstudio.com/manage/publishers/zhurong2020`
   (the publisher page created successfully in Step 1).
3. Clicked **"New extension"** → chose **"Visual Studio Code"** (as opposed
   to the other two options offered on the same button, "Visual Studio" and
   "Azure DevOps" — those are for different Marketplace artifact types
   entirely, not relevant here).
4. Uploaded the `.vsix` file directly through the browser upload dialog.

### Confirming it actually worked

The upload redirected back to the publisher management page without an
obvious success banner, so success was confirmed two ways:
1. The publisher's extension list now shows an entry: name
   "pyobfus — Python Code Obfuscator", version `0.1.0`, "works with" = `1`,
   updated "just now", availability "public".
2. An email arrived from `vsmarketplace@microsoft.com`: **"[Succeeded]
   Extension publish on Visual Studio Marketplace"** — "Extension
   Validation Successful... No issues were observed and the version 0.1.0
   is available for use in Visual Studio Marketplace."
3. The live listing itself resolves: `https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus`.

## For next time (v0.2.0 / M2, and beyond)

This runbook only covers the **first-ever** publish, which used "New
extension." The Marketplace UI presumably has a distinct **update** flow for
an already-listed extension's next version (upload against the existing
listing, not "New extension" again) — **not yet exercised**, since M2 is
still held for its own release-spacing gate as of this writing. Figure this
out live when M2 actually ships, and fold the answer back into this doc.

## Implication for M4 (CI auto-publish on `vscode-v*.*.*` tags)

A classic PAT is off the table until the Azure DevOps org-creation issue
resolves (on its own, or via a fix not yet tried). The newer
Entra-ID/federated-credential auto-publish method Microsoft now recommends
(PATs retire 2026-12-01) still requires an Azure DevOps organization as the
credential's home, so it does **not** sidestep this blocker either. Until
then, M4 either stays a manual `.vsix` upload process, or gets revisited if
the org-creation bug is ever retried and resolves.

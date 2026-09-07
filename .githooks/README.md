# Repo-local git hooks

This directory contains git hooks tracked alongside the repo. They are not
active by default in a fresh clone — git looks at `.git/hooks/` unless you
point it elsewhere.

## One-time setup per clone

```bash
git config core.hooksPath .githooks
```

After that, every clone-local git operation will pick up the hooks here.

## Hooks

### `pre-commit`

Two independent scans, each with its own allowlist and its own bypass.

#### Scan 1 — PII

Blocks 5 PII patterns from entering staged content:

- `诸嵘` (applicant real name)
- `陈启稚` (spouse real name)
- `qizhi_chen` (spouse email local-part)
- `身份证` (Chinese national ID literal)
- `/home/wuxia/` (workstation absolute path leak)

Origin: 2026-05-03 PII cleanup (see `docs/V0.4_EXECUTION_LOG.md` Sessions 13-15)
removed CCPC software-copyright filing materials from public history. This
hook is the structural guard against reintroduction.

**Allowlisted files** (legitimate references to the cleanup itself):

- `docs/V0.4_EXECUTION_LOG.md`
- `.githooks/pre-commit` (the hook contains the patterns themselves)
- `.githooks/README.md` (this file)
- `CLAUDE.md` (lists the patterns to document the hook for future maintainers)

To extend, edit `PII_ALLOWLIST_RE` at the top of `.githooks/pre-commit`.

**Bypass once** (for unusual cases):

```bash
PYOBFUS_ALLOW_PII=1 git commit ...
```

#### Scan 2 — credential material

Added 2026-09-07. The PII scan had no token coverage, so a credential pasted
into a file would have committed cleanly to this **public** repo.

Recognised shapes (high-signal prefixes only): Open VSX (`ovsxat_`), PyPI,
GitHub (`ghp_`/`github_pat_`), GitLab, npm, Anthropic, OpenAI, AWS
(`AKIA…`), Slack, Google API keys, and PEM private-key headers.

Deliberately **not** generic entropy matching. This repo ships a secret
*detector*, so broad heuristics would fight its own source and fixtures. The
pattern set was verified against every tracked file when added: zero
pre-existing matches.

On a hit the hook prints **`file:line` only, never the matched content** —
printing it would put the credential into the terminal and the shell history,
which is the thing the hook exists to prevent.

**Allowlisted files**: `.githooks/pre-commit` and `.githooks/README.md` — the
two files that enumerate the patterns themselves. To extend, edit
`SECRET_ALLOWLIST_RE`.

**Bypass once** — separate from the PII bypass on purpose, so waving through a
documented PII string does not silently also wave through a token:

```bash
PYOBFUS_ALLOW_SECRET=1 git commit ...
```

If a blocked credential was ever real, **rotate it**. Removing it from the
file is not a rotation.

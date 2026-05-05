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

To extend, edit `ALLOWLIST_RE` at the top of `.githooks/pre-commit`.

**Bypass once** (for unusual cases):

```bash
PYOBFUS_ALLOW_PII=1 git commit ...
```

# Python Baseline Template

**This is engineering scaffolding for new Python projects, not part of the pyobfus product.**

This directory holds the OpenSSF-passing-grade baseline that pyobfus itself uses, distilled into copyable files for future projects. The full design rationale lives in `~/projects/ENGINEERING_BASELINE.md` (workspace-wide).

## What you get

A bootstrap script that drops the following into a new project:

| File | Purpose | Tier |
|---|---|---|
| `.githooks/pre-commit` | PII scrub + lint check (templated for your project) | 0 |
| `SECURITY.md` | Vulnerability disclosure policy with placeholders | 0 |
| `.github/workflows/codeql.yml` | Static security analysis | 1 |
| `.github/codeql/codeql-config.yml` | Path-ignore for examples/tests | 1 |
| `.github/workflows/ci.yml` | Minimal CI (test + lint) | 0 |
| `CHANGELOG.md` | Keep a Changelog header | 0 |

CodeQL workflow comes pre-pinned to commit SHAs (correct as of 2026-05-09; refresh when stale).

## Usage

### One-shot bootstrap

```bash
# In an empty (or existing) project directory:
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/templates/python-baseline/bootstrap.sh | bash

# Or download first to inspect:
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/templates/python-baseline/bootstrap.sh -o bootstrap.sh
less bootstrap.sh
bash bootstrap.sh
```

The script is idempotent — running it twice won't clobber files you've customized; it skips files that already exist.

### Manual file-by-file

If the bootstrap script is too opinionated for your case, just `curl` individual files:

```bash
# CodeQL workflow
mkdir -p .github/workflows .github/codeql
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/.github/workflows/codeql.yml -o .github/workflows/codeql.yml
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/.github/codeql/codeql-config.yml -o .github/codeql/codeql-config.yml

# Pre-commit (genericized template)
mkdir -p .githooks
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/templates/python-baseline/pre-commit.template -o .githooks/pre-commit
chmod +x .githooks/pre-commit

# SECURITY.md template
curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/templates/python-baseline/SECURITY.md.template -o SECURITY.md
```

## After bootstrap

1. **Activate the pre-commit hook** (one-time per clone):
   ```bash
   git config core.hooksPath .githooks
   ```

2. **Edit `SECURITY.md`** — replace the `__PROJECT__` and `__EMAIL__` placeholders.

3. **Edit `.githooks/pre-commit`** — customize the PII pattern list for your project's data class. The template includes generic patterns (real names, emails, paths); adjust for what you actually need to block.

4. **Apply for OpenSSF Best Practices passing badge** when project has ~10 commits and ~1 month of activity:
   <https://www.bestpractices.dev/projects/new>

5. **Configure PyPI Trusted Publisher** (if publishing to PyPI):
   <https://pypi.org/manage/account/publishing/>

## Why this lives in pyobfus

pyobfus is the project that ran through the full OpenSSF passing process and accumulated battle-tested versions of these baseline files. Hosting them here means:

- One canonical source of truth (no drift across multiple template repos)
- The actual files in `pyobfus/.github/workflows/` etc. are themselves the templates
- Updates to pyobfus's baseline auto-propagate to anyone who re-runs the bootstrap

When the workspace gains a dedicated `python-baseline-template` repo, this directory will be deprecated in favor of that.

## Maintenance

When pyobfus's own baseline changes (new SHAs, new criteria covered), update the corresponding template file in this directory. Don't let the templates drift from what pyobfus actually runs in production — the whole value of this directory is "this is what the maintainer uses themselves."

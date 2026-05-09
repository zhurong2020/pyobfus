#!/usr/bin/env bash
# bootstrap.sh — drop the OpenSSF-passing baseline into a Python project
#
# Idempotent: skips files that already exist; never overwrites your work.
# Source files come from https://github.com/zhurong2020/pyobfus
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/zhurong2020/pyobfus/main/templates/python-baseline/bootstrap.sh | bash
#
# Or download first to inspect:
#   curl -fsSL .../bootstrap.sh -o bootstrap.sh && bash bootstrap.sh

set -eu

REPO="https://raw.githubusercontent.com/zhurong2020/pyobfus/main"
TEMPLATE_DIR="$REPO/templates/python-baseline"

PROJ_DIR="${1:-.}"
cd "$PROJ_DIR"

mkdir -p .github/workflows .github/codeql .githooks

# Helper: fetch only if local file doesn't exist.
fetch_if_absent() {
    local url="$1"
    local dest="$2"
    if [[ -f "$dest" ]]; then
        echo "  [skip] $dest (already exists)"
    else
        if curl -fsSL "$url" -o "$dest"; then
            echo "  [ok]   $dest"
        else
            echo "  [FAIL] $dest — could not fetch from $url"
            return 1
        fi
    fi
}

echo "Bootstrapping Python baseline into: $(pwd)"
echo ""

echo "Tier 1 — CodeQL static analysis (use as-is, SHAs pinned 2026-05-09):"
fetch_if_absent "$REPO/.github/workflows/codeql.yml"             ".github/workflows/codeql.yml"
fetch_if_absent "$REPO/.github/codeql/codeql-config.yml"          ".github/codeql/codeql-config.yml"

echo ""
echo "Tier 0 — Pre-commit hook + SECURITY.md (CUSTOMIZE after bootstrap):"
fetch_if_absent "$TEMPLATE_DIR/pre-commit.template"               ".githooks/pre-commit"
chmod +x .githooks/pre-commit 2>/dev/null || true
fetch_if_absent "$TEMPLATE_DIR/SECURITY.md.template"              "SECURITY.md"

echo ""
echo "Tier 0 — CHANGELOG header (if missing):"
if [[ ! -f CHANGELOG.md ]]; then
    cat > CHANGELOG.md <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Security
EOF
    echo "  [ok]   CHANGELOG.md"
else
    echo "  [skip] CHANGELOG.md (already exists)"
fi

echo ""
echo "============================================================"
echo "Bootstrap complete."
echo ""
echo "Next steps:"
echo "  1. git config core.hooksPath .githooks"
echo "  2. Edit SECURITY.md — replace __PROJECT__ and __EMAIL__"
echo "  3. Edit .githooks/pre-commit — customize PII patterns"
echo "  4. Add a CI workflow (.github/workflows/ci.yml — see pyobfus for example)"
echo "  5. After ~10 commits / ~1 month: apply for OpenSSF passing badge at"
echo "     https://www.bestpractices.dev/projects/new"
echo ""
echo "Reference: ~/projects/ENGINEERING_BASELINE.md (workspace-wide)"
echo "============================================================"

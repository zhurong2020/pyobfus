#!/usr/bin/env bash
# Static checks shared by CI and local development.
#
# CI's "Lint and Type Check" and "Docs build" jobs call this script, so the
# paths below are the only list. Before it existed, AGENTS.md told
# contributors to run `black pyobfus/` while CI checked eleven paths; a file
# under tests/ that only CI looked at turned main red for nine pushes on
# 2026-09-20, and every open pull request with it.
#
# Usage: scripts/check.sh [lint|docs|all]   (default: all)
#
# Uses ./venv/bin/python when it exists, otherwise `python` on PATH (CI).
# Override with PYTHON=/path/to/python.
#
# Tests are not run here: the four pytest roots and the Python/OS matrix stay
# in CI and in the commands listed in AGENTS.md.

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${PYTHON:-}" ]]; then
    if [[ -x venv/bin/python ]]; then
        PYTHON=venv/bin/python
    else
        PYTHON=python
    fi
fi

# Everything black and ruff check.
LINT_PATHS=(
    pyobfus/
    pyobfus_pro/
    pyobfus_runtime/pyobfus_runtime/
    pyobfus_runtime/tests/
    pyobfus_mcp/pyobfus_mcp/
    tests/
    integration_tests/
    benchmarks/llm_resistance/
    examples/
    scripts/
)

# Every shipped source package. Tests stay covered by pytest and lint; they
# are not part of the public typed surface.
TYPED_PACKAGES=(
    pyobfus/
    pyobfus_pro/
    pyobfus_runtime/pyobfus_runtime/
    pyobfus_mcp/pyobfus_mcp/
)

step() {
    printf '\n==> %s\n' "$*"
}

run_lint() {
    step "black --check"
    "$PYTHON" -m black --version
    "$PYTHON" -m black --check "${LINT_PATHS[@]}"

    step "ruff check"
    "$PYTHON" -m ruff --version
    "$PYTHON" -m ruff check "${LINT_PATHS[@]}"

    step "mypy"
    "$PYTHON" -m mypy "${TYPED_PACKAGES[@]}"

    step "discovery metadata is valid JSON"
    "$PYTHON" -m json.tool docs/.well-known/ai-catalog.json > /dev/null
}

run_docs() {
    step "Agent guide twins match"
    cmp --silent llms.txt docs/llms.txt

    # README.md is the package long_description. PyPI resolves relative links
    # against the project page, so they 404 there while looking fine on GitHub.
    step "README links survive PyPI rendering"
    "$PYTHON" scripts/check_readme_links.py

    # --strict turns link warnings into failures. Do not add --quiet: it drops
    # warnings before --strict counts them, and a broken link then passes.
    step "mkdocs build --strict"
    "$PYTHON" -m mkdocs build --strict
}

target="${1:-all}"
case "$target" in
    lint) run_lint ;;
    docs) run_docs ;;
    all)  run_lint; run_docs ;;
    *)
        echo "usage: scripts/check.sh [lint|docs|all]" >&2
        exit 2
        ;;
esac

step "OK: $target checks passed"

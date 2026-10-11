"""Conservative AST-only hardcoded-secret screening, with no value in findings.

Keep high-signal shapes aligned with .githooks/pre-commit (plus Stripe).
Regex spellings deliberately avoid credential-shaped source: the public-repo
hook must accept this detector without a credential-scan bypass. No entropy
heuristic or new dependencies. Shapes are medium; names alone are weaker info.
"""

from __future__ import annotations

import ast
import re
from typing import Dict, List, Set, Tuple

_SHAPES = [
    ("Open VSX token", r"ovsx[a]t_"),
    ("PyPI token", r"pypi-[A]gEIcHlwaS5vcmc"),
    ("GitHub token", r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    ("GitLab token", r"glpat-[A-Za-z0-9_-]{15,}"),
    ("npm token", r"npm_[A-Za-z0-9]{30,}"),
    ("Anthropic API key", r"sk-ant-api[0-9]{2}-"),
    ("OpenAI API key", r"sk-proj-[A-Za-z0-9_-]{20,}"),
    ("AWS access key", r"AKIA[0-9A-Z]{16}(?![0-9A-Z])"),
    ("Slack token", r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("Google API key", r"AIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])"),
    ("Stripe secret key", r"(?:sk_live|rk_live|rk_test)_[A-Za-z0-9]{16,}"),
    ("PEM private key", r"-{5}BEGIN [A-Z ]*PRIVATE KEY-{5}"),
]
_PATTERNS = [(kind, re.compile(pattern)) for kind, pattern in _SHAPES]
_FIELD_NAMES = {
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "key",
    "secret",
    "secret_key",
    "authorization",
    "access_token",
    "bearer",
    "client_secret",
    "github_token",
    "openai_api_key",
    "token_type",
}

SUGGESTION = (
    "Obfuscation does not hide string values: this value will appear unchanged "
    "in delivered artifacts. Read it at runtime from environment variables or "
    "a secret manager. If it was ever shipped or committed, rotate it; deletion "
    "is not rotation. This is only a coarse screen; use gitleaks or detect-secrets "
    "for a full scan."
)


def _ignored(value: str) -> bool:
    value = value.strip()
    lower = value.lower()
    return (
        len(value) < 8
        or len(set(lower)) == 1
        or lower in _FIELD_NAMES
        or bool(re.match(r"^[a-z][a-z0-9+.-]*://", lower))
        or bool(re.fullmatch(r"\$?\{[^{}]+\}|<[^<>]+>", value))
        or bool(
            re.search(
                r"(?:^|[-_\s])(your|changeme|example|dummy|test|placeholder|xxx+)(?:$|[-_\s])",
                lower,
            )
        )
    )


# Name-only evidence is intentionally narrow: metadata and ordinary keys are
# common in real projects. Split word segments rather than matching substrings.
_KEY_QUALIFIERS = {
    "api",
    "secret",
    "private",
    "access",
    "signing",
    "encryption",
    "auth",
    "client",
    "app",
    "master",
}
_METADATA_SUFFIXES = {
    "file",
    "path",
    "dir",
    "url",
    "uri",
    "endpoint",
    "env",
    "var",
    "name",
    "field",
    "header",
    "type",
    "prefix",
    "id",
    "hint",
    "label",
    "message",
    "msg",
    "help",
    "format",
    "pattern",
    "regex",
}
_FILE_SUFFIXES = (
    ".json",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".env",
    ".pem",
    ".key",
    ".crt",
    ".db",
    ".log",
)


def _sensitive_name(name: str) -> bool:
    # Include acronym boundaries (APIKey) and regular camelCase (apiKey).
    segmented = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    segmented = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", segmented)
    words = re.split(r"[_-]+", segmented.lower().strip("_-"))
    if words[-1] in _METADATA_SUFFIXES:
        return False
    return (
        any(word in {"password", "passwd", "secret", "token"} for word in words)
        or any(
            word == "key" and previous in _KEY_QUALIFIERS
            for previous, word in zip(words, words[1:])
        )
        or any(word in {qualifier + "key" for qualifier in _KEY_QUALIFIERS} for word in words)
    )


def _ignored_info(value: str) -> bool:
    """Exclude ordinary data only from weak name-based evidence, never shapes."""
    return (
        _ignored(value)
        or any(char.isspace() for char in value)
        or bool(re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", value))
        or bool(re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", value))
        or value.startswith(("/", "./", "../", "~/"))
        or value.lower().endswith(_FILE_SUFFIXES)
    )


def find_secret_literals(tree: ast.AST) -> List[Tuple[ast.Constant, str, str]]:
    """Return location, severity and fixed type only; never return literal values.

    Direct literal contexts only: assignments, defaults, keywords and dict
    values. Annotation strings, docstrings and interpolated f-strings are
    excluded even when their text resembles a token.
    """
    ignored: Set[ast.AST] = set()
    names: Dict[ast.AST, List[str]] = {}

    def bind(value: ast.AST, name: str) -> None:
        names.setdefault(value, []).append(name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                ignored.update(ast.walk(node.body[0]))
        if isinstance(node, ast.JoinedStr):
            ignored.update(ast.walk(node))
        if isinstance(node, (ast.AnnAssign, ast.arg)) and node.annotation:
            ignored.update(ast.walk(node.annotation))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
            ignored.update(ast.walk(node.returns))
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bind(node.value, target.id)
                elif isinstance(target, ast.Attribute):
                    bind(node.value, target.attr)
        elif isinstance(node, ast.AnnAssign) and node.value:
            if isinstance(node.target, ast.Name):
                bind(node.value, node.target.id)
            elif isinstance(node.target, ast.Attribute):
                bind(node.value, node.target.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            bind(node.value, node.arg)
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    bind(value, key.value)
        elif isinstance(node, ast.arguments):
            positional = node.posonlyargs + node.args
            for arg, default in zip(positional[-len(node.defaults) :], node.defaults):
                bind(default, arg.arg)
            for arg, kw_default in zip(node.kwonlyargs, node.kw_defaults):
                if kw_default is not None:
                    bind(kw_default, arg.arg)

    findings = []
    for node in ast.walk(tree):
        if node in ignored or not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if _ignored(node.value):
            continue
        kind = next((kind for kind, pattern in _PATTERNS if pattern.search(node.value)), None)
        if kind:
            findings.append((node, "medium", kind))
        elif any(
            (_sensitive_name(name) and not _ignored_info(node.value))
            or (
                name.lower() == "authorization"
                and node.value.lower().startswith("bearer ")
                and not _ignored_info(node.value[7:])
            )
            for name in names.get(node, [])
        ):
            findings.append((node, "info", "Credential-like name"))
    return findings

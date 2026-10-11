"""AST secret screening and output privacy; fake shapes generated at runtime."""

import inspect
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core.preflight import CAT_HARDCODED_SECRET, PreflightChecker, format_report_text


def shapes():
    tail = "aB3cD4eF5gH6iJ7kL8mN9pQ0rS1tU2vW3xY4z"
    return [
        "ovsx" + "at_" + tail,
        "pypi-" + "AgEIcHlwaS5vcmc" + tail,
        *["gh" + letter + "_" + tail for letter in "pousr"],
        "github_" + "pat_" + tail,
        "glpat-" + tail,
        "npm_" + tail,
        "sk-ant-" + "api03-" + tail,
        "sk-proj-" + tail,
        "AKIA" + "1234567890ABCDEF",
        "xoxb-" + tail,
        "AIza" + tail[:35],
        "sk_live_" + tail,
        "rk_live_" + tail,
        "-----BEGIN " + "RSA PRIVATE KEY-----\n" + tail + "\n-----END PRIVATE KEY-----",
    ]


def scan(tmp_path, source):
    path = tmp_path / "app.py"
    path.write_text(source, encoding="utf-8")
    report = PreflightChecker(offline=True).check_path(path)
    risks = [r for r in report.risks if r.category == CAT_HARDCODED_SECRET]
    return path, report, risks


@pytest.mark.parametrize("value", shapes())
def test_shapes_once_medium(tmp_path, value):
    _, report, risks = scan(tmp_path, f"API_KEY = {value!r}\n")
    assert len(risks) == 1
    assert risks[0].severity == "medium"
    assert risks[0].snippet == ""
    assert value not in report.to_json()
    assert report.exit_code() == 0
    assert "First move 1 hardcoded secret" in report.ai_hint
    assert "Low risk" not in report.ai_hint


@pytest.mark.parametrize(
    "source",
    [
        'DB_PASSWORD = "Cedar9!Maple"',
        'class Settings:\n    API_KEY = "Cedar9!Maple"',
        'def connect(password="Cedar9!Maple"): pass',
        'async def connect(*, passwd="Cedar9!Maple"): pass',
        'client(api_key="Cedar9!Maple")',
        'TOKEN: str = "Cedar9!Maple"',
        'headers = {"Authorization": "Bearer Cedar9!Maple"}',
        'settings = {"secret": "Cedar9!Maple"}',
        'apikey = "Cedar9!Maple"',
        'serviceApiKey = "Cedar9!Maple"',
        'obj.secret = "Cedar9!Maple"',
    ],
)
def test_name_contexts_info(tmp_path, source):
    _, report, risks = scan(tmp_path, source)
    assert len(risks) == 1
    assert risks[0].severity == "info"
    assert report.exit_code() == 0
    assert report.ai_hint.startswith("Low risk.")
    assert "1 string literal(s) are assigned to credential-like names" in report.ai_hint
    assert risks[0].message == "String literal assigned to a credential-like name."


@pytest.mark.parametrize(
    "value",
    [
        "",
        "your-api-key",
        "<token>",
        "xxxxxxxxxxxx",
        "changeme",
        "example",
        "dummy",
        "test",
        "placeholder",
        "aaaaaaaaaaaa",
        "${VAR}",
        "{var}",
        "dummy-password",
        "example-token",
        "password",
        "SECRET_KEY",
        "access_token",
        "https://service.invalid/token",
        "token_type",
        "Bearer <token>",
    ],
)
def test_placeholder_and_field_exclusions(tmp_path, value):
    _, _, risks = scan(tmp_path, f"SECRET_KEY = {value!r}\n")
    # Bearer placeholders are excluded in their specific header context.
    if value.startswith("Bearer "):
        _, _, risks = scan(tmp_path, f"headers = {{'Authorization': {value!r}}}\n")
    assert not risks


@pytest.mark.parametrize(
    "source",
    [
        'API_KEY = os.environ["API_KEY"]',
        'TOKEN = os.getenv("TOKEN")',
        'TOKEN = environ.get("TOKEN", "")',
        "PASSWORD = get_password()",
        'API_KEY = f"prefix-{value}"',
        'PASSWORD_FIELD = "password"',
        'TOKEN_URL = "https://service.invalid/auth"',
        'SECRET_KEY_NAME = "SECRET_KEY"',
        'token_type = "bearer"',
        'SQL = "SELECT something FROM somewhere"',
        'IMAGE = "aGVsbG8gdGhpcyBpcyBhbiBpbWFnZQ=="',
        'SHA256 = "' + "abc01234" * 8 + '"',
    ],
)
def test_non_literal_and_ordinary_data(tmp_path, source):
    assert not scan(tmp_path, source)[2]


def test_docstrings_annotations_comments_and_fstrings(tmp_path):
    value = shapes()[2]
    source = (
        f"{value!r}\n# {value}\n"
        f"def f(arg: {value!r}) -> {value!r}:\n    {value!r}\n    pass\n"
        f"class C:\n    {value!r}\n    token: {value!r}\n"
        f'x = f"{value}{{variable}}"\n'
    )
    assert not scan(tmp_path, source)[2]


def test_first_expression_call_is_scanned(tmp_path):
    assert len(scan(tmp_path, f"client(api_key={shapes()[2]!r})")[2]) == 1


def test_excluded_files(tmp_path):
    folder = tmp_path / "tests"
    folder.mkdir()
    (folder / "fixture.py").write_text(f"TOKEN = {shapes()[2]!r}\n")
    report = PreflightChecker(
        exclude_patterns=["tests/**"], report_excluded=True, effective_config={}, offline=True
    ).check_path(tmp_path)
    assert not report.risks
    assert len(report.excluded_risks) == 1
    assert report.excluded_risks[0].category == CAT_HARDCODED_SECRET
    assert report.exit_code() == 0
    assert "First move" not in report.ai_hint


def test_all_output_surfaces_hide_values(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "pyobfus_mcp"))
    from pyobfus_mcp.tools import check_obfuscation_risks

    values = shapes() + ["Cedar9!Maple", "Bearer Spruce8!Birch"]
    source = "\n".join(f"TOKEN_{i} = {value!r}" for i, value in enumerate(values[:-1]))
    source += f"\nheaders = {{'Authorization': {values[-1]!r}}}"
    path, report, risks = scan(tmp_path, source)
    assert len(risks) == len(values)
    runner = CliRunner(
        **({"mix_stderr": False} if "mix_stderr" in inspect.signature(CliRunner).parameters else {})
    )
    text = runner.invoke(main, ["--check", str(path), "--offline", "--no-config"])
    sarif_path = tmp_path / "report.sarif"
    result = runner.invoke(
        main,
        ["--check", str(path), "--offline", "--no-config", "--json", "--sarif", str(sarif_path)],
    )
    assert text.exit_code == result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "Low risk" not in payload["ai_hint"]
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    mcp = check_obfuscation_risks(str(path), use_project_config=False)
    assert mcp["status"] == "success"
    assert mcp["category_counts"][CAT_HARDCODED_SECRET] == len(values)
    outputs = [
        text.stdout,
        format_report_text(report),
        result.stdout,
        sarif_path.read_text(),
        json.dumps(mcp),
    ]
    for value in values:
        assert all(value not in output for output in outputs)
    for risk in risks:
        assert risk.snippet == ""
        assert "rotate" in risk.suggestion
        assert "gitleaks" in risk.suggestion
        assert "Pro" not in risk.suggestion


def test_secret_hint_preserves_high_exit(tmp_path):
    _, report, risks = scan(tmp_path, f"TOKEN = {shapes()[2]!r}\neval(source)\n")
    assert len(risks) == 1
    assert report.exit_code() == 1
    assert report.ai_hint.startswith("First move 1 hardcoded secret")
    assert "Low risk" not in report.ai_hint


def test_detector_does_not_flag_own_metadata():
    root = Path(__file__).resolve().parents[1]
    report = PreflightChecker(offline=True).check_path(root / "pyobfus")
    assert not [r for r in report.risks if r.category == CAT_HARDCODED_SECRET]


@pytest.mark.parametrize(
    "source",
    [
        'CACHE_KEY = "user_profile_cache"',
        'SORT_KEY = "created_at"',
        'PRIMARY_KEY = "customer_id"',
        'TOKEN_ENV = "MYAPP_SERVICE_TOKEN"',
        'TOKEN_ENDPOINT = "/oauth/token"',
        'PASSWORD_HINT = "At least 8 characters"',
        'TOKENIZER_NAME = "bert-base-uncased"',
        'secretary_name = "Alice Johnson"',
        'SESSION_COOKIE_KEY = "sessionid"',
        'def load(tokenizer_path="models/tokenizer.json"): pass',
    ],
)
def test_review_adversarial_examples(tmp_path, source):
    assert not scan(tmp_path, source)[2]


@pytest.mark.parametrize(
    "source",
    [
        'DB_PASSWORD = "Tr0ub4dor&3-prod"',
        'SECRET_KEY = "django-insecure-5f#k2!q9z"',
        'APP_TOKEN = "aB3cD4eF5gH6iJ7kL8mN9pQ0rS1t"',
        'headers = {"Authorization": "Bearer abcdef0123456789"}',
        'def connect(password="hunter2hunter2"): pass',
        'client(api_key="AbC123xyz789QwE")',
        'class Settings:\n    API_KEY = "AbC123xyz789QwE"',
        'TOKEN: str = "AbC123xyz789QwE"',
    ],
)
def test_review_true_positives(tmp_path, source):
    risks = scan(tmp_path, source)[2]
    assert len(risks) == 1
    assert risks[0].severity == "info"


@pytest.mark.parametrize(
    "name",
    [
        "tokenizer",
        "tokens",
        "secretary",
        "CACHE_KEY",
        "SORT_KEY",
        "PRIMARY_KEY",
        "SESSION_COOKIE_KEY",
    ],
)
def test_non_credential_name_segments(tmp_path, name):
    assert not scan(tmp_path, f'{name} = "AbC123xyz789QwE"')[2]


@pytest.mark.parametrize(
    "suffix",
    [
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
    ],
)
def test_metadata_suffixes(tmp_path, suffix):
    assert not scan(tmp_path, f'TOKEN_{suffix} = "AbC123xyz789QwE"')[2]


@pytest.mark.parametrize(
    "qualifier",
    [
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
    ],
)
@pytest.mark.parametrize("style", ["snake", "hyphen", "camel", "joined"])
def test_qualified_keys(tmp_path, qualifier, style):
    name = {
        "snake": qualifier + "_key",
        "hyphen": qualifier + "-key",
        "camel": qualifier + "Key",
        "joined": qualifier + "key",
    }[style]
    assert len(scan(tmp_path, f'settings = {{{name!r}: "AbC123xyz789QwE"}}')[2]) == 1


@pytest.mark.parametrize(
    "value",
    [
        "A helpful password message",
        "MYAPP_SERVICE_TOKEN",
        "/credential",
        "./credential",
        "../credential",
        "~/credential",
        "created_at",
        "user_profile_cache",
    ]
    + [
        "credential" + ext
        for ext in (
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
    ],
)
def test_info_value_exclusions(tmp_path, value):
    assert not scan(tmp_path, f"TOKEN = {value!r}")[2]


@pytest.mark.parametrize("decoration", ["\n", "/", "./", "../", "~/", ".json", ".key"])
def test_info_exclusions_do_not_suppress_shapes(tmp_path, decoration):
    value = shapes()[2]
    value = value + decoration if decoration.startswith(".") else decoration + value
    risks = scan(tmp_path, f"TOKEN_FILE = {value!r}")[2]
    assert len(risks) == 1
    assert risks[0].severity == "medium"


def test_info_hint_preserves_other_risk_guidance(tmp_path):
    _, report, _ = scan(tmp_path, 'TOKEN = "AbC123xyz789QwE"\neval(source)')
    assert report.exit_code() == 1
    assert report.ai_hint.startswith("High-risk patterns found.")
    assert "1 string literal(s) are assigned to credential-like names" in report.ai_hint
    assert "First move" not in report.ai_hint


def test_mixed_hint_counts_only_medium_as_secrets(tmp_path):
    _, report, risks = scan(tmp_path, f'A = {shapes()[2]!r}\nTOKEN = "AbC123xyz789QwE"')
    assert len(risks) == 2
    assert report.ai_hint.startswith("First move 1 hardcoded secret")
    assert "1 string literal(s) are assigned to credential-like names" in report.ai_hint

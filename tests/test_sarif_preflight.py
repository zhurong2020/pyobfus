"""Tests for the SARIF 2.1.0 preflight projection (0.5.21).

Covers the acceptance checklist in docs/V0.5.21_RELEASE_PLAN.md: valid SARIF
shape (schema-validated offline against a vendored fixture), rule/severity
mapping, one-based region conversion, deterministic fingerprints, config-
excluded suppression without exit-code change, parse-error notifications,
privacy (no source/absolute-path/secret leakage), and CLI contract
preservation with text and --json.
"""

import json
from pathlib import Path

import jsonschema
import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.core import sarif
from pyobfus.core.preflight import (
    CAT_DYNAMIC_ATTR,
    CAT_DYNAMIC_EXEC,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    PreflightReport,
    Risk,
)

SCHEMA_PATH = Path(__file__).parent / "fixtures" / "sarif-schema-2.1.0.json"


@pytest.fixture(scope="module")
def sarif_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def runner():
    return CliRunner()


def _risk(category=CAT_DYNAMIC_EXEC, severity=SEVERITY_HIGH, file="src/a.py", line=3, col=10, **kw):
    return Risk(
        category=category,
        severity=severity,
        file=file,
        line=line,
        col=col,
        message=kw.get("message", "msg"),
        suggestion=kw.get("suggestion", "fix"),
        snippet=kw.get("snippet", ""),
    )


def _report(root="src", risks=None, excluded=None, parse_errors=None):
    r = PreflightReport(root=root)
    r.risks = risks or []
    r.excluded_risks = excluded or []
    r.parse_errors = parse_errors or []
    return r


# --- 1 + 10: valid SARIF 2.1.0, schema-validated offline -----------------


class TestSchemaShape:
    def test_top_level_shape(self, sarif_schema):
        doc = sarif.build_sarif(_report(risks=[_risk()]), "1.2.3")
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        assert doc["version"] == "2.1.0"
        assert doc["$schema"].endswith("sarif-schema-2.1.0.json")
        assert len(doc["runs"]) == 1

    def test_driver_metadata(self):
        doc = sarif.build_sarif(_report(risks=[_risk()]), "9.9.9")
        driver = doc["runs"][0]["tool"]["driver"]
        assert driver["name"] == "pyobfus"
        assert driver["version"] == "9.9.9"
        assert driver["semanticVersion"] == "9.9.9"
        assert driver["informationUri"].startswith("https://")

    def test_empty_report_is_valid(self, sarif_schema):
        doc = sarif.build_sarif(_report(), "1.0.0")
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        assert doc["runs"][0]["results"] == []


# --- 2: rule IDs and severity mapping ------------------------------------


class TestRulesAndSeverity:
    def test_all_categories_have_rules(self):
        doc = sarif.build_sarif(_report(), "1.0.0")
        rules = doc["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 12
        ids = {r["id"] for r in rules}
        assert all(i.startswith("PYOBFUS/") for i in ids)
        assert "PYOBFUS/dynamic_exec" in ids
        assert "PYOBFUS/dependency_advisory" in ids

    @pytest.mark.parametrize(
        "severity,level",
        [
            (SEVERITY_HIGH, "error"),
            (SEVERITY_MEDIUM, "warning"),
            (SEVERITY_LOW, "note"),
            (SEVERITY_INFO, "note"),
        ],
    )
    def test_severity_maps_to_level(self, severity, level):
        doc = sarif.build_sarif(_report(risks=[_risk(severity=severity)]), "1.0.0")
        assert doc["runs"][0]["results"][0]["level"] == level

    def test_result_ruleid_matches_category(self):
        doc = sarif.build_sarif(_report(risks=[_risk(category=CAT_DYNAMIC_ATTR)]), "1.0.0")
        assert doc["runs"][0]["results"][0]["ruleId"] == "PYOBFUS/dynamic_attr"


# --- 3: one-based region conversion --------------------------------------


class TestRegionConversion:
    def test_col_offset_is_one_based_in_sarif(self):
        doc = sarif.build_sarif(_report(risks=[_risk(line=5, col=10)]), "1.0.0")
        region = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] == 5  # line already 1-based
        assert region["startColumn"] == 11  # col_offset 10 -> column 11

    def test_project_level_finding_has_no_region(self, sarif_schema):
        # Advisories use line=0 -> artifactLocation only, no region.
        doc = sarif.build_sarif(_report(risks=[_risk(line=0, col=0)]), "1.0.0")
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        phys = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        assert "region" not in phys
        assert "artifactLocation" in phys


# --- 4: deterministic fingerprints ---------------------------------------


class TestFingerprints:
    def test_stable_for_identical_finding(self):
        d1 = sarif.build_sarif(_report(risks=[_risk()]), "1.0.0")
        d2 = sarif.build_sarif(_report(risks=[_risk()]), "9.9.9")  # version irrelevant
        fp1 = d1["runs"][0]["results"][0]["partialFingerprints"]
        fp2 = d2["runs"][0]["results"][0]["partialFingerprints"]
        assert fp1 == fp2
        assert sarif.FINGERPRINT_KEY in fp1

    def test_changes_with_location(self):
        d1 = sarif.build_sarif(_report(risks=[_risk(line=3)]), "1.0.0")
        d2 = sarif.build_sarif(_report(risks=[_risk(line=99)]), "1.0.0")
        assert (
            d1["runs"][0]["results"][0]["partialFingerprints"]
            != d2["runs"][0]["results"][0]["partialFingerprints"]
        )


# --- 5: config-excluded suppression, no exit-code change -----------------


class TestSuppression:
    def test_excluded_risk_is_suppressed(self, sarif_schema):
        doc = sarif.build_sarif(_report(excluded=[_risk(severity=SEVERITY_HIGH)]), "1.0.0")
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        result = doc["runs"][0]["results"][0]
        assert result["suppressions"][0]["kind"] == "external"
        assert result["properties"]["pyobfus.excluded"] is True

    def test_included_risk_not_suppressed(self):
        doc = sarif.build_sarif(_report(risks=[_risk()]), "1.0.0")
        assert "suppressions" not in doc["runs"][0]["results"][0]


# --- 6: parse-error invocation notification ------------------------------


class TestParseErrors:
    def test_parse_error_sets_invocation_and_notification(self, sarif_schema):
        rep = _report(parse_errors=["/abs/secret/path/broken.py: SyntaxError: bad token"])
        doc = sarif.build_sarif(rep, "1.0.0")
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        inv = doc["runs"][0]["invocations"][0]
        assert inv["executionSuccessful"] is False
        assert inv["exitCode"] == 2
        notes = inv["toolExecutionNotifications"]
        assert len(notes) == 1
        # Safe generic message; never the raw exception text.
        assert "SyntaxError" not in notes[0]["message"]["text"]
        # Relativised to basename; never the absolute path.
        uri = notes[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri == "broken.py"

    def test_no_parse_error_execution_successful(self):
        doc = sarif.build_sarif(_report(risks=[_risk()]), "1.0.0")
        inv = doc["runs"][0]["invocations"][0]
        assert inv["executionSuccessful"] is True
        assert inv["exitCode"] == 1  # high finding
        assert "toolExecutionNotifications" not in inv


# --- 7: privacy -- no source, absolute path, or secret leakage -----------


class TestPrivacy:
    def test_no_snippet_or_secret_or_absolute_path(self):
        rep = _report(
            root="/home/dev/project",
            risks=[
                _risk(
                    file="/home/dev/project/app.py",
                    snippet='API_KEY = "sk-live-SUPERSECRET"',
                    message='getattr(o, "SUPERSECRET")',
                )
            ],
        )
        blob = json.dumps(sarif.build_sarif(rep, "1.0.0"))
        assert "SUPERSECRET" not in blob
        assert "sk-live" not in blob
        assert "/home/dev" not in blob
        assert "file://" not in blob
        # The artifact URI is relative.
        assert '"uri": "app.py"' in blob


# --- 8 + 9: CLI contract preservation and error handling -----------------


class TestCliWiring:
    def test_sarif_with_json_preserves_json_contract(self, runner, tmp_path, sarif_schema):
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text('def f(x):\n    return eval("x")\n')
        out = tmp_path / "out.sarif"
        result = runner.invoke(main, ["--check", str(src), "--sarif", str(out), "--json"])
        # exit code driven by findings (eval => high => 1), not by SARIF
        assert result.exit_code == 1
        payload = json.loads(result.output)  # stdout is still the pyobfus JSON
        assert payload["version"] == 1
        assert "risks" in payload
        # SARIF written separately and schema-valid
        doc = json.loads(out.read_text())
        jsonschema.Draft7Validator(sarif_schema).validate(doc)

    def test_sarif_with_text_output(self, runner, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text("def f(x):\n    return x\n")
        out = tmp_path / "out.sarif"
        result = runner.invoke(main, ["--check", str(src), "--sarif", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        assert "risk" in result.output.lower() or "pyobfus" in result.output.lower()

    def test_sarif_requires_check(self, runner, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 1\n")
        result = runner.invoke(
            main, [str(src), "-o", str(tmp_path / "o.py"), "--sarif", str(tmp_path / "x.sarif")]
        )
        assert result.exit_code != 0
        assert "only valid with --check" in result.output

    def test_sarif_directory_target_refused(self, runner, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 1\n")
        adir = tmp_path / "adir"
        adir.mkdir()
        result = runner.invoke(main, ["--check", str(src), "--sarif", str(adir)])
        assert result.exit_code != 0

    def test_sarif_write_failure_structured_error(self, runner, tmp_path):
        # Parent of the sarif path is a regular file, so mkdir/write fails.
        src = tmp_path / "a.py"
        src.write_text("x = 1\n")
        blocker = tmp_path / "blocker"
        blocker.write_text("not a dir")
        bad = blocker / "out.sarif"
        result = runner.invoke(main, ["--check", str(src), "--sarif", str(bad), "--json"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["error_type"] == "sarif_write_error"


# --- atomic write --------------------------------------------------------


class TestAtomicWrite:
    def test_write_sarif_produces_valid_file(self, tmp_path, sarif_schema):
        out = tmp_path / "nested" / "report.sarif"
        sarif.write_sarif(_report(risks=[_risk()]), out, "1.0.0")
        assert out.exists()
        doc = json.loads(out.read_text())
        jsonschema.Draft7Validator(sarif_schema).validate(doc)
        # No leftover temp files in the target directory.
        leftovers = [p.name for p in out.parent.iterdir() if p.name != "report.sarif"]
        assert leftovers == []

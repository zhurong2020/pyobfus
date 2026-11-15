"""Pure acceptance logic; no Nuitka or Windows dependency."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "windows_acceptance",
    Path(__file__).resolve().parents[1] / "scripts/validate_windows_nuitka_delivery.py",
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize(
    "statuses, expected",
    [
        ({"A": "pass", "C": "blocked"}, "pass"),
        ({"A": "unknown", "F": "blocked"}, "partial"),
        ({"A": "fail", "B": "blocked"}, "fail"),
        ({"A": "blocked"}, "blocked"),
        ({"A": "partial", "F": "blocked"}, "partial"),
    ],
)
def test_aggregation(statuses, expected):
    assert runner.aggregate(statuses) == expected


@pytest.mark.parametrize(
    "payload",
    [
        {"mapping": {"x": "y"}},
        {"modules": {"app": {"renamed": "original"}}},
        {"unmapped_trace": "public source too"},
        {"note": "Traceback (most recent call last):"},
        {"note": 'File "main.py", line 3, in x'},
        {"nested": [{"stderr": "anything"}]},
        {"note": "-" * 5 + "BEGIN PRIVATE" + " KEY" + "-" * 5},
    ],
)
def test_private_content_refused(payload):
    with pytest.raises(ValueError):
        runner.safe_evidence(payload)


def test_public_evidence_allowed():
    runner.safe_evidence(
        {
            "private_hashes": {"mapping.json": "a" * 64},
            "public_frame_names": ["quote_order"],
            "command": ["--mapping", "<work>/private/mapping.json"],
        }
    )


def test_delivery_audit(tmp_path):
    private, source, delivery = [tmp_path / n for n in ("private", "source", "delivery")]
    for folder in (private, source, delivery):
        folder.mkdir()
    (source / "main.py").write_text("print('public')")
    (private / "mapping.json").write_text('{"private": true}')
    (delivery / "main.exe").write_bytes(b"compiled executable")
    assert runner.audit_delivery(delivery, private, source) == []
    (delivery / "renamed.bin").write_bytes((private / "mapping.json").read_bytes())
    (delivery / "main.py").write_text("source")
    (delivery / "x.build").mkdir()
    (delivery / "trace.txt").write_text("trace")
    assert set(runner.audit_delivery(delivery, private, source)) == {
        "renamed.bin",
        "main.py",
        "x.build",
        "trace.txt",
    }

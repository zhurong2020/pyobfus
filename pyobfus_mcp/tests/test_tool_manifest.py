"""Tests for P2-21 tool-description integrity (rug-pull resistance)."""

from __future__ import annotations

import json

import pytest

from pyobfus_mcp.tool_manifest import (
    _diff_manifests,
    compute_live_manifest,
    load_shipped_manifest,
    main,
    verify_integrity,
)


class TestComputeLiveManifest:
    def test_returns_all_eight_tools(self) -> None:
        manifest = compute_live_manifest()
        names = [t["name"] for t in manifest["tools"]]
        assert len(names) == 8
        assert names == sorted(names), "tools must be sorted by name"
        assert "protect_project" in names
        assert "check_obfuscation_risks" in names

    def test_each_tool_has_required_fields(self) -> None:
        manifest = compute_live_manifest()
        for tool in manifest["tools"]:
            assert tool["name"]
            assert tool["description"]
            assert tool["input_schema"] is not None
            assert isinstance(tool["meta"], dict)

    def test_digest_is_deterministic(self) -> None:
        m1 = compute_live_manifest()
        m2 = compute_live_manifest()
        assert m1["digest"] == m2["digest"]
        assert len(m1["digest"]) == 64  # sha256 hex

    def test_digest_changes_when_a_description_changes(self) -> None:
        manifest = compute_live_manifest()
        tools = json.loads(json.dumps(manifest["tools"]))  # deep copy
        tools[0]["description"] = tools[0]["description"] + " (tampered)"
        import hashlib

        from pyobfus_mcp.tool_manifest import _canonicalize

        tampered_digest = hashlib.sha256(_canonicalize(tools).encode("utf-8")).hexdigest()
        assert tampered_digest != manifest["digest"]


class TestVerifyIntegrity:
    def test_matches_the_committed_shipped_manifest(self) -> None:
        """This is the real regression guard: if a PR changes a tool's
        description/schema/meta without regenerating tool_manifest.json
        (`pyobfus-mcp-verify --generate`), this test fails."""
        result = verify_integrity()
        assert result["match"] is True, (
            f"live tool registration no longer matches the shipped manifest -- "
            f"run `pyobfus-mcp-verify --generate` and commit the result. "
            f"diff: {result.get('diff')}"
        )

    def test_shipped_manifest_is_loadable_and_well_formed(self) -> None:
        shipped = load_shipped_manifest()
        assert "digest" in shipped
        assert "tools" in shipped
        assert len(shipped["tools"]) == 8


class TestDiffManifests:
    def test_no_diff_when_identical(self) -> None:
        tools = [{"name": "a", "description": "d", "input_schema": {}, "meta": {}}]
        assert _diff_manifests(tools, tools) == []

    def test_detects_removed_tool(self) -> None:
        shipped = [{"name": "a", "description": "d", "input_schema": {}, "meta": {}}]
        live: list = []
        diff = _diff_manifests(shipped, live)
        assert any("removed" in d and "'a'" in d for d in diff)

    def test_detects_new_tool(self) -> None:
        shipped: list = []
        live = [{"name": "a", "description": "d", "input_schema": {}, "meta": {}}]
        diff = _diff_manifests(shipped, live)
        assert any("new" in d and "'a'" in d for d in diff)

    def test_detects_changed_description(self) -> None:
        shipped = [{"name": "a", "description": "original", "input_schema": {}, "meta": {}}]
        live = [{"name": "a", "description": "tampered", "input_schema": {}, "meta": {}}]
        diff = _diff_manifests(shipped, live)
        assert len(diff) == 1
        assert "'a'" in diff[0] and "description" in diff[0]

    def test_detects_changed_meta_but_not_description(self) -> None:
        shipped = [
            {"name": "a", "description": "d", "input_schema": {}, "meta": {"tier": "community"}}
        ]
        live = [
            {"name": "a", "description": "d", "input_schema": {}, "meta": {"tier": "pro_funnel"}}
        ]
        diff = _diff_manifests(shipped, live)
        assert "meta" in diff[0] and "description" not in diff[0]


class TestCliEntryPoint:
    def test_verify_exits_zero_on_match(self, capsys: pytest.CaptureFixture) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0
        assert "OK" in capsys.readouterr().out

    def test_generate_writes_manifest_and_returns(
        self, tmp_path, monkeypatch, capsys: pytest.CaptureFixture
    ) -> None:
        # --generate does not sys.exit (unlike the verify path). Redirects
        # the write target to a tmp path -- this must NOT touch the real
        # committed pyobfus_mcp/tool_manifest.json as a side effect of
        # running the test suite.
        import pyobfus_mcp.tool_manifest as tm

        fake_path = tmp_path / "tool_manifest.json"
        monkeypatch.setattr(tm, "_manifest_path", lambda: fake_path)

        main(["--generate"])
        out = capsys.readouterr().out
        assert "Wrote" in out
        assert "8 tools" in out
        assert fake_path.exists()

        written = json.loads(fake_path.read_text(encoding="utf-8"))
        assert len(written["tools"]) == 8
        assert written["digest"] == compute_live_manifest()["digest"]

"""Exercise the real MCP build tool -> JSON CLI entitlement boundary."""

from datetime import datetime
import json

import pytest

from pyobfus_mcp.tools import protect_project, generate_pyobfus_config

pytest.importorskip("pyobfus._entitlement", reason="installed Core has no Pro access gate")


@pytest.mark.parametrize("access", ["none", "trial", "license"])
@pytest.mark.parametrize("from_config", [False, True])
def test_mcp_pro_build_entitlement(tmp_path, monkeypatch, access, from_config):
    monkeypatch.chdir(tmp_path)
    if access == "trial":
        from pyobfus.trial import start_trial

        assert start_trial()["success"]
    elif access == "license":
        from pyobfus_pro.license import cache_license

        # Synthetic verifier cache: no license server is called by either process.
        cache_license(
            {
                "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
                "type": "professional",
                "expires": "2099-12-31",
                "verified": datetime.now().isoformat(),
            }
        )
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text('def greeting():\n    return "hello"\n')
    if from_config:
        (tmp_path / "pyobfus.yaml").write_text(
            "obfuscation:\n  level: pro\n  string_encryption: true\n"
        )
    out = tmp_path / "out"
    result = protect_project(
        str(src), str(out), preset=None if from_config else "commercial", verify=False
    )
    assert result["ai_hint"]
    assert "next_tool" in result
    if access == "none":
        assert result["status"] == "error", result
        assert "license" in json.dumps(result).lower()
        assert not out.exists()
    else:
        assert result["status"] == "success", result
        assert (out / "mod.py").exists()
    assert "PYOB-AAAA-BBBB-CCCC-DDDD" not in json.dumps(result)


def test_mcp_pro_config_generation_stays_read_only_and_free(tmp_path):
    (tmp_path / "mod.py").write_text("print(1)\n")
    result = generate_pyobfus_config(str(tmp_path), preset_override="commercial")
    assert result["status"] == "success"


def test_mcp_ci_secret_inherited_with_mock_server(tmp_path, monkeypatch):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    import sys
    from pyobfus_mcp import tools

    key = "PYOB-AAAA-BBBB-CCCC-DDDD"
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"valid":true,"activation":"ci","expires_at":null}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", key)
    monkeypatch.chdir(tmp_path)
    # Use the real CLI subprocess, pointing only its verifier at a local mock.
    monkeypatch.setattr(
        tools,
        "_obfuscate_command",
        lambda: [
            sys.executable,
            "-c",
            (
                "from pyobfus_pro import license; "
                f"license.LICENSE_API_URL='http://127.0.0.1:{server.server_port}/api/verify'; "
                "from pyobfus.cli import main; main()"
            ),
        ],
    )
    src = tmp_path / "src"
    src.mkdir()
    for n in range(3):
        (src / f"mod{n}.py").write_text('print("hello")\n')
    try:
        result = protect_project(str(src), str(tmp_path / "out"), preset="commercial", verify=False)
        assert result["status"] == "success", result
        assert calls == [{"license_key": key, "activation": "ci"}]
        assert key not in json.dumps(result)
        assert not (tmp_path / ".pyobfus" / "license.json").exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

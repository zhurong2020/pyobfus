"""IndexNow CI helper contracts, without network access."""

import io
import json
import urllib.error
from unittest.mock import MagicMock

import pytest

from scripts import indexnow_submit as submit

KEY = "0f5fb35e631b28ef475c62df09d73cdd"
BASE = submit.DOCS_BASE
ARGS = ["--host", "pyobfus.readthedocs.io", "--key", KEY, "--key-location", BASE + KEY + ".txt"]


@pytest.fixture(autouse=True)
def network(monkeypatch):
    mock = MagicMock()
    mock.return_value.__enter__.return_value.status = 200
    monkeypatch.setattr(submit.urllib.request, "urlopen", mock)
    return mock


def test_changed_docs(monkeypatch, capsys, network):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            "docs/index.md\ndocs/X.md\ndocs/a/b.md\ndocs/a/index.md\ndocs/X.md\n"
            "docs/internal/private.md\ndocs/internal/nested/private.md\ndocs/image.png\n"
            "README.md\ndocs/CLAUDE_MD_HISTORY.md\ndocs/../secret.md\n"
        ),
    )
    assert submit.main(ARGS + ["--from-changed-docs", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["urlList"] == [
        BASE,
        BASE + "X/",
        BASE + "a/b/",
        BASE + "a/",
    ]
    network.assert_not_called()


def test_sitemap(tmp_path):
    path = tmp_path / "sitemap.xml"
    path.write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://example.org/a/</loc></url></urlset>"
    )
    assert submit.sitemap_urls(path) == ["https://example.org/a/"]


def test_scope_and_cap(capsys):
    rejected = [
        "https://other.org/en/latest/a/",
        "https://pyobfus.readthedocs.io/en/old/",
        BASE + "../private/",
        BASE + "%2e%2e/private/",
        "https://pyobfus.readthedocs.io/en/latest-other/a/",
    ]
    assert submit.scoped_urls(rejected + [BASE, BASE], "pyobfus.readthedocs.io", BASE + KEY) == [
        BASE
    ]
    assert capsys.readouterr().err.count("dropping") == len(rejected)
    urls = [BASE + str(i) + "/" for i in range(10001)]
    assert len(submit.scoped_urls(urls, "pyobfus.readthedocs.io", BASE + KEY)) == 10000
    assert "10,000" in capsys.readouterr().err


@pytest.mark.parametrize("status", [200, 202])
def test_payload(status, network, capsys):
    network.return_value.__enter__.return_value.status = status
    assert submit.main(ARGS + [BASE, "--strict"]) == 0
    request = network.call_args.args[0]
    assert json.loads(request.data) == {
        "host": "pyobfus.readthedocs.io",
        "key": KEY,
        "keyLocation": BASE + KEY + ".txt",
        "urlList": [BASE],
    }
    assert request.full_url == submit.ENDPOINT
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json; charset=utf-8"
    assert request.get_header("User-agent") == submit.USER_AGENT
    assert network.call_args.kwargs == {"timeout": 20}
    assert f"HTTP {status}: accepted" in capsys.readouterr().out


@pytest.mark.parametrize("status", [400, 403, 422, 429, 500])
@pytest.mark.parametrize("strict", [False, True])
def test_http_error(status, strict, network, capsys):
    network.side_effect = urllib.error.HTTPError(submit.ENDPOINT, status, "error", {}, None)
    assert submit.main(ARGS + [BASE] + (["--strict"] if strict else [])) == int(strict)
    assert f"HTTP {status}" in capsys.readouterr().out


@pytest.mark.parametrize("strict", [False, True])
def test_network_error(strict, network):
    network.side_effect = urllib.error.URLError("offline")
    assert submit.main(ARGS + [BASE] + (["--strict"] if strict else [])) == int(strict)


@pytest.mark.parametrize(
    "args",
    [
        [],
        ARGS,
        ARGS + [BASE, "--from-nav"],
        ARGS + ["--from-nav", "--from-changed-docs"],
        ARGS + [BASE, "--key-location", "https://other.org/key.txt"],
        ARGS + [BASE, "--key", "invalid!"],
    ],
)
def test_usage(args, network):
    with pytest.raises(SystemExit) as exc:
        submit.main(args)
    assert exc.value.code == 2
    network.assert_not_called()


def test_invalid_sitemap(tmp_path, network):
    path = tmp_path / "bad.xml"
    path.write_text("<invalid")
    with pytest.raises(SystemExit) as exc:
        submit.main(ARGS + ["--from-sitemap", str(path)])
    assert exc.value.code == 2
    network.assert_not_called()


def test_empty(monkeypatch, network):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert submit.main(ARGS + ["--from-changed-docs"]) == 0
    network.assert_not_called()


def test_nav():
    paths = list(submit.nav_paths())
    assert "docs/index.md" in paths
    assert "docs/guides/protect-python-before-selling.md" in paths
    assert all("://" not in path for path in paths)
    assert BASE in list(submit.docs_urls(paths))

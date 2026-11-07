"""CI-only IndexNow notifications; no dependencies or package imports."""

import argparse
import fnmatch
import json
import posixpath
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS_BASE = "https://pyobfus.readthedocs.io/en/latest/"
ENDPOINT = "https://api.indexnow.org/indexnow"
USER_AGENT = "pyobfus-indexnow/1 (+https://github.com/zhurong2020/pyobfus)"
MEANINGS = {
    200: "accepted",
    202: "accepted; key validation pending",
    400: "bad request",
    403: "key not valid",
    422: "URL/host mismatch",
    429: "too many requests",
}


def config_section(name):
    """Read an indented section of this repository's block-style mkdocs.yml."""
    active = False
    for line in (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + ":"):
            active = True
            continue
        if active and line and not line[0].isspace() and not line.startswith("#"):
            break
        if active and line.strip() and not line.lstrip().startswith("#"):
            yield line.strip()


def excluded(path):
    # Support the current exclude_docs block's directory and glob rules.
    # Hidden paths are excluded by MkDocs by default; internal is always private.
    if path.startswith("internal/") or any(p.startswith(".") for p in path.split("/")):
        return True
    result = False
    for rule in config_section("exclude_docs"):
        negate = rule.startswith("!")
        pattern = rule.lstrip("!/")
        if pattern.endswith("/"):
            matches = path.startswith(pattern)
        else:
            matches = fnmatch.fnmatchcase(path, pattern)
        if matches:
            result = not negate
    return result


def docs_urls(paths):
    for value in paths:
        path = value.strip()
        if not path.startswith("docs/") or not path.endswith(".md"):
            continue
        relative = path[5:]
        if ".." in relative.split("/") or "\\" in relative or excluded(relative):
            continue
        page = PurePosixPath(relative).with_suffix("")
        if page.name == "index":
            page = page.parent
        suffix = "" if str(page) == "." else quote(str(page), safe="/") + "/"
        yield DOCS_BASE + suffix


def nav_paths():
    # The repository uses block-style nav entries with local .md scalar values.
    for line in config_section("nav"):
        match = re.search(r":\s*['\"]?([^'\"\s]+\.md)['\"]?\s*$", line)
        if match and "://" not in match[1]:
            yield "docs/" + match[1]


def sitemap_urls(path):
    return [
        node.text.strip()
        for node in ET.parse(path).iter()
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text and node.text.strip()
    ]


def scoped_urls(urls, host, location):
    directory = unquote(urlsplit(location).path).rsplit("/", 1)[0] + "/"
    accepted = []
    seen = set()
    for url in urls:
        try:
            parsed = urlsplit(url)
            decoded = unquote(parsed.path)
            normalized = posixpath.normpath(decoded)
            if decoded.endswith("/"):
                normalized += "/" if normalized != "/" else ""
            valid = (
                parsed.scheme in {"http", "https"}
                and parsed.netloc == host
                and not parsed.fragment
                and "\\" not in decoded
                and normalized.startswith(directory)
            )
        except ValueError:
            valid = False
        if not valid:
            print(f"Warning: dropping out-of-scope URL: {url}", file=sys.stderr)
        elif url not in seen:
            seen.add(url)
            accepted.append(url)
    if len(accepted) > 10000:
        print("Warning: truncating submission to 10,000 URLs", file=sys.stderr)
    return accepted[:10000]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--key-location", required=True)
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--from-sitemap", type=Path)
    sources.add_argument("--from-changed-docs", action="store_true")
    sources.add_argument(
        "--from-nav", action="store_true", help="submit all local MkDocs nav pages"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("urls", nargs="*")
    args = parser.parse_args(argv)
    try:
        location = urlsplit(args.key_location)
        if (
            location.scheme not in {"http", "https"}
            or location.netloc != args.host
            or not location.hostname
            or location.username
            or location.port
            or location.query
            or location.fragment
            or location.path.endswith("/")
            or not location.path
            or ".." in unquote(location.path).split("/")
        ):
            raise ValueError("key location must be a file URL on --host")
        if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", args.key):
            raise ValueError("key must contain 8–128 letters, digits or hyphens")
        source = args.from_sitemap or args.from_changed_docs or args.from_nav
        if bool(args.urls) == bool(source):
            raise ValueError("provide URLs or exactly one --from-* source")
        if args.from_sitemap:
            urls = sitemap_urls(args.from_sitemap)
        elif args.from_changed_docs:
            urls = docs_urls(sys.stdin)
        elif args.from_nav:
            urls = docs_urls(nav_paths())
        else:
            urls = args.urls
        payload = {
            "host": args.host,
            "key": args.key,
            "keyLocation": args.key_location,
            "urlList": scoped_urls(urls, args.host, args.key_location),
        }
    except (ValueError, OSError, ET.ParseError) as exc:
        parser.error(str(exc))
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    if not payload["urlList"]:
        print("No eligible URLs; nothing submitted.")
        return 0
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
    except (urllib.error.URLError, OSError) as exc:
        print(f"IndexNow network failure: {exc}")
        return 1 if args.strict else 0
    print(f"IndexNow HTTP {status}: {MEANINGS.get(status, 'unexpected response')}")
    return 1 if args.strict and status not in (200, 202) else 0


if __name__ == "__main__":
    sys.exit(main())

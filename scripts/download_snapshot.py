#!/usr/bin/env python3
"""Download / adoption snapshot for pyobfus and its sibling channels.

Prints, for each PyPI package, the last N days of *non-mirror* daily downloads
with release days marked (from git tags), plus the non-release-day median so a
release-day spike is never read as growth.  Then the VS Code Marketplace,
Open VSX and GitHub Action attribution counters.

Usage:  python scripts/download_snapshot.py [--days 14] [--no-gh]

Stdout is plain ASCII on purpose (Windows consoles).  No credentials needed;
the optional GitHub code search uses the ``gh`` CLI's own login.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import subprocess
import sys
import time
import urllib.request

UA = "pyobfus-download-snapshot (https://github.com/zhurong2020/pyobfus)"
PACKAGES = {
    # package -> git tag prefix that marks its releases
    "pyobfus": "v0.",
    "pyobfus-mcp": "mcp-v",
    "pyobfus-runtime": "runtime-v",
}
EXT_PUBLISHER, EXT_NAME = "zhurong2020", "pyobfus"


def http_json(url: str, data: bytes | None = None, headers: dict | None = None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:  # pypistats rate-limits (429)
            if e.code == 429 and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            raise


def release_days() -> dict[str, set[str]]:
    """UTC dates of tags, keyed by package (tag timestamps are converted to UTC
    because pypistats buckets by UTC day)."""
    out = subprocess.run(
        ["git", "tag", "--format=%(creatordate:unix) %(refname:short)"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    days: dict[str, set[str]] = {p: set() for p in PACKAGES}
    for line in out.splitlines():
        ts, tag = line.split(" ", 1)
        day = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%d")
        for pkg, prefix in PACKAGES.items():
            if tag.startswith(prefix):
                days[pkg].add(day)
    return days


def pypi_section(pkg: str, days: int, rel: set[str]) -> None:
    data = http_json(f"https://pypistats.org/api/packages/{pkg}/overall?mirrors=false")["data"]
    series = [(r["date"], r["downloads"]) for r in data if r["category"] == "without_mirrors"]
    series.sort()
    recent = series[-days:]
    print(f"== PyPI {pkg} (no mirrors, last {len(recent)} days; * = release day, + = day after)")
    line = []
    for d, n in recent:
        prev = (dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat()
        mark = "*" if d in rel else ("+" if prev in rel else "")
        line.append(f"{d[5:]}={n}{mark}")
    print("   " + " ".join(line))
    for window in (7, 30):
        w = series[-window:]
        quiet = [
            n
            for d, n in w
            if d not in rel
            and (dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat() not in rel
        ]
        rel_n = sum(1 for d, _ in w if d in rel)
        med = statistics.median(quiet) if quiet else 0
        print(
            f"   last {window:>2}d: total={sum(n for _, n in w):>5}  release days={rel_n}  "
            f"quiet days={len(quiet):>2}  quiet median={med:.0f}  quiet sum={sum(quiet)}"
        )
    print(f"   data through {series[-1][0]} (pypistats lags about one day)")


def marketplace_section() -> None:
    body = json.dumps(
        {
            "filters": [{"criteria": [{"filterType": 7, "value": f"{EXT_PUBLISHER}.{EXT_NAME}"}]}],
            "flags": 914,
        }
    ).encode()
    d = http_json(
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1",
        },
    )
    ext = d["results"][0]["extensions"][0]
    st = {s["statisticName"]: s["value"] for s in ext.get("statistics", [])}
    print(
        f"== VS Code Marketplace {EXT_PUBLISHER}.{EXT_NAME}: version={ext['versions'][0]['version']} "
        f"installs={st.get('install', 0):.0f} updates={st.get('updateCount', 0):.0f} "
        f"ratings={st.get('ratingcount', 0) or 0:.0f}"
    )
    print(
        "   installs is the only adoption number; updates and downloads are mostly existing installs"
    )


def openvsx_section() -> None:
    d = http_json(f"https://open-vsx.org/api/{EXT_PUBLISHER}/{EXT_NAME}")
    print(
        f"== Open VSX {EXT_PUBLISHER}.{EXT_NAME}: version={d.get('version')} "
        f"downloads={d.get('downloadCount')} reviews={d.get('reviewCount')}"
    )
    print(
        "   downloadCount counts every vsix fetch (mirrors/crawlers included); not additive with Marketplace"
    )


def action_section() -> None:
    try:
        out = subprocess.run(
            [
                "gh",
                "search",
                "code",
                "uses: zhurong2020/pyobfus-action",
                "--json",
                "repository",
                "--jq",
                "map(.repository.nameWithOwner)|unique|length",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        n = out.stdout.strip() if out.returncode == 0 else f"n/a ({out.stderr.strip()[:80]})"
    except Exception as e:  # noqa: BLE001 - reporting only
        n = f"n/a ({e})"
    print(f"== GitHub Action attribution: repos referencing pyobfus-action = {n}")
    print("   GitHub code search only indexes visible repos; measures visibility, not adoption")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--no-gh", action="store_true", help="skip the GitHub code search")
    a = ap.parse_args()
    print(f"pyobfus download snapshot  {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC")
    rel = release_days()
    for pkg in PACKAGES:
        try:
            pypi_section(pkg, a.days, rel[pkg])
        except Exception as e:  # noqa: BLE001
            print(f"== PyPI {pkg}: fetch failed ({e})")
        if pkg == "pyobfus-runtime":
            print(
                "   caveat: every CI job that installs a pyobfus wheel resolves pyobfus-runtime from PyPI,"
            )
            print("   so its count is dominated by this repo's own CI matrix, not by users")
    for fn in (marketplace_section, openvsx_section):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"== {fn.__name__}: fetch failed ({e})")
    if not a.no_gh:
        action_section()
    print(
        "Read the quiet-day median, not the totals: releases spike the same day and fall back in 2-3 days."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

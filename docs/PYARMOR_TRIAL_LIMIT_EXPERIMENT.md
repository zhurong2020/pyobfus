# PyArmor Trial Code-Size Limit — Reproducible Experiment

**Date**: 2026-05-09
**Tester**: Rong Zhu (pyobfus maintainer)
**PyArmor version**: 9.2.4 (trial license)
**Python**: 3.12.3
**Platform**: Linux x86_64 (WSL2 Ubuntu)

## Why this experiment exists

PyArmor's free / trial tier officially "can't obfuscate big scripts" but the [official documentation](https://pyarmor.readthedocs.io/en/latest/licenses.html) never quantifies what counts as "big." This experiment measures the threshold empirically and provides reproducible commands so anyone can verify or re-test after future PyArmor updates.

This file is the source-of-truth for the same finding cited in the launch articles (`_drafts/article-01-claude-code-mcp-integration.md` Section 1, the CN trio in `_drafts/post-cn-ready/`).

## Setup

```bash
mkdir -p /tmp/pyarmor-limit-test
cd /tmp/pyarmor-limit-test
python3 -m venv venv
source venv/bin/activate
pip install pyarmor                # installs latest, was 9.2.4 on test date
pyarmor --version                  # confirms "trial" + "Can't obfuscate big script and mix str"
```

`pyarmor --version` self-reports:

```
Pyarmor 9.2.4 (trial), 000000, non-profits

License Type    : pyarmor-trial
License No.     : pyarmor-vax-000000
License Product : non-profits

BCC Mode        : No
RFT Mode        : No
CI/CD Mode      : No

Notes
* Can't obfuscate big script and mix str
This is trial license
```

## Result 1 — Real-world test on pyobfus's own `cli.py` (1665 lines)

```bash
cp /path/to/pyobfus/pyobfus/cli.py cli_test_1665lines.py
pyarmor gen cli_test_1665lines.py
```

Output:
```
INFO     obfuscating file cli_test_1665lines.py
ERROR    out of license
```

Result: **❌ FAIL.** PyArmor trial cannot obfuscate this file.

## Result 2 — Synthetic-Python binary search

Test files generated programmatically. Each function is a 5-line block (`def` / 3 body lines / blank line), so a file with N total lines contains N/5 functions. This produces standard sparse Python shape representative of typical real-world modules.

| Lines | Bytes | Result |
|---|---|---|
| 100 | 1,160 | ✅ obfuscate scripts OK |
| 500 | 5,470 | ✅ obfuscate scripts OK |
| 600 | 6,630 | ✅ obfuscate scripts OK |
| 700 | 7,790 | ✅ obfuscate scripts OK |
| 800 | 8,950 | ✅ obfuscate scripts OK |
| 850 | 9,530 | ✅ obfuscate scripts OK |
| 900 | 10,110 | ✅ obfuscate scripts OK |
| 910 | 10,226 | ✅ obfuscate scripts OK |
| 925 | 10,400 | ✅ obfuscate scripts OK |
| 930 | 10,458 | ✅ obfuscate scripts OK |
| 935 | 10,516 | ✅ obfuscate scripts OK |
| **940** | **10,574** | ❌ **ERROR out of license** |
| 945 | 10,632 | ❌ ERROR out of license |
| 950 | 10,690 | ❌ ERROR out of license |
| 1000 | 11,270 | ❌ ERROR out of license |
| 1500 | 17,070 | ❌ ERROR out of license |
| 2000 | 22,870 | ❌ ERROR out of license |
| 4000 | 46,070 | ❌ ERROR out of license |
| 1665 (real cli.py) | 51,237 | ❌ ERROR out of license |

**Threshold**: 935 lines pass, 940 lines fail. The cutoff sits somewhere in the 935–939 line range for typical sparse Python.

## Result 3 — Is the limit by line count or by byte count?

Test: same 900-line file but with each line padded with ~80-char comments. Byte size inflated 6.6×.

| Source shape | Lines | Bytes | Result |
|---|---|---|---|
| Sparse (5-line functions) | 900 | 10,110 | ✅ |
| **Same 900 lines, dense comments** | **900** | **66,810** | **✅ still OK** |

A 67 KB file at 900 lines passes; an 11 KB file at 940 lines fails.

**Conclusion**: PyArmor trial measures by **line count** (or AST node count proportional to line count), not by raw byte size.

## Result 4 — PyArmor's error message

The error is a flat:

```
ERROR    out of license
```

PyArmor does NOT disclose:
- The threshold number
- That the threshold is line-count-based
- Which paid tier ("Basic", "Pro", etc.) lifts the limit
- A link to the pricing page

To learn the threshold a user must either find it through trial-and-error (this experiment) or read the [license comparison table](https://pyarmor.readthedocs.io/en/latest/licenses.html), which only reveals that the gating capability is named "Big Script / Mix String" and is paywalled — not the threshold itself.

## Reproducing this experiment in 60 seconds

```bash
mkdir -p /tmp/pyarmor-limit-test && cd /tmp/pyarmor-limit-test
python3 -m venv venv && source venv/bin/activate
pip install --quiet pyarmor

gen_test() {
  local lines=$1; local funcs=$((lines / 5)); local out="syn_${lines}lines.py"; : > "$out"
  for i in $(seq 0 $((funcs - 1))); do
    printf 'def f%d():\n    x = %d\n    y = %d + 1\n    return x + y\n\n' "$i" "$i" "$i" >> "$out"
  done
}

# These two commands demonstrate the threshold:
gen_test 935 && pyarmor gen syn_935lines.py    # PASSES
gen_test 940 && pyarmor gen syn_940lines.py    # FAILS with "ERROR out of license"
```

## Implications for pyobfus's positioning

- The "Big Script" feature gate exists at all paid PyArmor tiers; the Free tier blanket-blocks it.
- For typical sparse Python the threshold is around **935–940 lines**.
- A typical real-world Python module easily exceeds this. pyobfus's own `cli.py` is 1665 lines.
- For projects with even one ~1000+ line file, PyArmor effectively requires immediate upgrade to a paid tier.
- This is not a PyArmor critique; it's a documented business decision. The point of recording it here is that pyobfus operates in the segment **where this paywall meaningfully changes the buy-vs-build calculus**, and we want public, verifiable data backing that claim.

## When to re-test

Re-run this experiment when:
1. PyArmor releases a major version (10.x or beyond) — the threshold may shift.
2. PyArmor publicly announces a free-tier policy change.
3. A reader / reviewer questions the 935–940 threshold cited in launch articles or this repo.

## Related references

- PyArmor official license comparison: <https://pyarmor.readthedocs.io/en/latest/licenses.html>
- PyArmor docs landing: <https://pyarmor.readthedocs.io/>
- This experiment cited inline in: `_drafts/article-01-claude-code-mcp-integration.md` Section 1 + `_drafts/post-cn-ready/{tech_empowerment,zhihu,v2ex}.md`
- Verified-facts table reference: `docs/POST_V0.4_TODO.md` § "Verified facts baseline"

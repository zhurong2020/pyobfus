"""Single Windows x64 / CPython 3.12 / Community Nuitka acceptance.

Only evidence/ is public. Everything else remains in a fresh temporary root.
Non-Windows execution is a labelled local smoke, never Windows acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Any
import xml.etree.ElementTree as ET

FIXTURE = Path(__file__).resolve().parents[1] / "examples/delivery_reference"
# Split so the repository credential scanner does not flag the detector itself.
_PEM = b"-" * 5
STEPS = tuple(f"D{i}" for i in range(1, 11))


def aggregate(results: dict[str, str]) -> str:
    """C alone may be blocked; unknown never means clean."""
    required = [v for k, v in results.items() if k != "C"]
    if "fail" in required:
        return "fail"
    if "unknown" in required or "partial" in required:
        return "partial"
    if "blocked" in required:
        return "blocked"
    return "pass"


def hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def audit_delivery(root: Path, private: Path, source: Path) -> list[str]:
    """Reject diagnostic material, project source and key/state files."""
    forbidden_hashes = set(hashes(private).values()) | {
        hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob("*.py")
    }
    findings = []
    for p in sorted(root.rglob("*")):
        name = p.relative_to(root).as_posix()
        lower = name.lower()
        if (
            p.is_symlink()
            or any(part.endswith(".build") for part in p.parts)
            or any(s in lower for s in ("mapping", "provenance", "trace", "build-report"))
            or p.name.lower() in ("build.json", "license.json", "trial.json")
            or p.suffix.lower() in (".py", ".pyc", ".pem", ".key", ".log")
        ):
            findings.append(name)
        elif p.is_file():
            data = p.read_bytes()
            if (
                hashlib.sha256(data).hexdigest() in forbidden_hashes
                or _PEM + b"BEGIN PRIVATE" + b" KEY" + _PEM in data
                or _PEM + b"BEGIN RSA PRIVATE" + b" KEY" + _PEM in data
            ):
                findings.append(name)
    return findings


def safe_evidence(value: Any) -> None:
    """Fail closed on trace/mapping payloads, secrets, or unrestricted logs.

    File names, hashes and command paths may name private files; contents may not.
    Callers project unmap results to public original frame names before writing.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {
                "mapping",
                "unmapped_trace",
                "raw_trace",
                "traceback",
                "stdout",
                "stderr",
                "source_code",
                "protected_source",
                "license_key",
                "original_to_obfuscated",
                "obfuscated_to_original",
                "line_map",
                "modules",
                "file_mappings",
                "identifier_map",
            }:
                raise ValueError("Private payload refused")
            safe_evidence(item)
    elif isinstance(value, list):
        for item in value:
            safe_evidence(item)
    elif isinstance(value, str):
        if any(
            s in value
            for s in (
                "Traceback (most recent call last)",
                "-----BEGIN",
                "PYOB-",
                '"unmapped_trace":',
                '"obfuscated_to_original":',
            )
        ) or re.search(r'File ".*", line \d+', value):
            raise ValueError("Private content refused")


class Blocked(Exception):
    pass


class Unknown(Exception):
    pass


class Runner:
    def __init__(self, work: Path, evidence: Path):
        self.work, self.evidence = work, evidence
        work.mkdir(parents=True, exist_ok=False)
        self.private = work / "private"
        self.private.mkdir()
        self.env = dict(os.environ)
        for key in list(self.env):
            if key.startswith("PYOBFUS_") or key in ("PYTHONPATH", "PYTHONHOME"):
                self.env.pop(key)
        for key in (
            "HOME",
            "USERPROFILE",
            "TEMP",
            "TMP",
            "TMPDIR",
            "LOCALAPPDATA",
            "APPDATA",
            "XDG_CACHE_HOME",
            "NUITKA_CACHE_DIR",
            "PIP_CACHE_DIR",
        ):
            folder = work / "state" / key.lower()
            folder.mkdir(parents=True)
            self.env[key] = str(folder)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.env["PYTHONIOENCODING"] = "utf-8"
        self.report: dict[str, Any] = {
            "scope": "Windows x64 / CPython 3.12 / Nuitka standalone / Community",
            "local_smoke": sys.platform != "win32",
            "environment": {
                "os": platform.platform(),
                "os_build": platform.version(),
                "python": sys.version,
                "machine": platform.machine(),
                "consumer": "same hosted builder; Python preinstalled; not a clean target",
            },
            "steps": {},
            "commands": [],
            "limitations": [
                "Frozen payload internals are uninspected",
                "Pro C blocked: no isolated Pro licence; never attempted",
                "Python 3.12 selected; actual patch recorded",
            ],
        }
        self.build_seconds = 0.0
        self.diagnostic_seconds = 0.0
        self.source = work / "source"
        self.protected = work / "protected"
        self.delivery = work / "delivery"
        self.consumer = work / "consumer"
        self.baseline = ""

    def run(
        self,
        args: list[Any],
        cwd: Path | None = None,
        *,
        expected: int | None = 0,
        build: bool = False,
        consumer: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        args = [str(a) for a in args]
        budget = 1200 - self.build_seconds if build else 600 - self.diagnostic_seconds
        if budget <= 0:
            raise Blocked("Cumulative build/diagnostic budget exhausted")
        env = dict(self.env)
        if consumer:
            env["PATH"] = os.pathsep.join(
                filter(
                    None,
                    [
                        str(Path(env.get("SystemRoot", "C:/Windows")) / "System32"),
                        env.get("SystemRoot", ""),
                    ],
                )
            )
        start = time.monotonic()
        event = {
            "command": [a.replace(str(self.work), "<work>") for a in args],
            "cwd": str(cwd or self.work).replace(str(self.work), "<work>"),
        }
        try:
            process = subprocess.Popen(
                args,
                cwd=cwd or self.work,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                out, err = process.communicate(timeout=budget)
            except subprocess.TimeoutExpired:
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True,
                        timeout=15,
                    )
                process.kill()
                process.communicate()
                raise
            result = subprocess.CompletedProcess(args, process.returncode, out, err)
            event["exit_code"] = result.returncode
            (self.private / f"command-{len(self.report['commands']) + 1}.log").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
        except subprocess.TimeoutExpired:
            event["timeout"] = True
            raise Blocked("Cumulative build/diagnostic time limit reached") from None
        finally:
            elapsed = time.monotonic() - start
            event["seconds"] = round(elapsed, 3)
            self.report["commands"].append(event)
            if build:
                self.build_seconds += elapsed
            else:
                self.diagnostic_seconds += elapsed
        if expected is not None and result.returncode != expected:
            raise RuntimeError(
                f"Command {len(self.report['commands'])} exit {result.returncode}; see private log"
            )
        return result

    def cli(self, *args: Any, expected: int | None = 0) -> subprocess.CompletedProcess[str]:
        return self.run([sys.executable, "-m", "pyobfus", *args], expected=expected)

    def d1(self) -> None:
        env = self.report["environment"]
        env["pyobfus"] = metadata.version("pyobfus")
        try:
            env["nuitka_version"] = metadata.version("nuitka")
        except metadata.PackageNotFoundError:
            env["nuitka_version"] = "unavailable"
        self.run([sys.executable, "-m", "pip", "check"])
        if sys.platform != "win32":
            env["installation"] = "local editable interpreter allowed for smoke only"
            raise Unknown("Local Linux smoke; public wheel and Windows toolchain not accepted")
        if (
            sys.version_info[:2] != (3, 12)
            or platform.machine().lower() not in ("amd64", "x86_64")
            or sys.prefix == sys.base_prefix
        ):
            raise Blocked("Requires fresh x64 CPython 3.12 venv")
        if env["pyobfus"] != "0.14.0" or metadata.version("nuitka") != "4.3.1":
            raise Blocked("Frozen public tool versions do not match")
        direct = metadata.distribution("pyobfus").read_text("direct_url.json")
        if direct:
            raise Blocked("Public index install required; direct/editable installation refused")
        wheels = self.private / "wheels"
        self.run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--index-url",
                "https://pypi.org/simple",
                "--no-deps",
                "--only-binary=:all:",
                "--dest",
                wheels,
                "pyobfus==0.14.0",
            ]
        )
        wheel = next(wheels.glob("pyobfus-0.14.0-*.whl"))
        self.report["wheel"] = {
            "filename": wheel.name,
            "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "index": "https://pypi.org/simple",
        }
        with urllib.request.urlopen(
            "https://pypi.org/pypi/pyobfus/0.14.0/json", timeout=30
        ) as response:
            public = json.load(response)
        published = next(item for item in public["urls"] if item["filename"] == wheel.name)
        self.report["wheel"]["url"] = published["url"]
        if published["digests"]["sha256"] != self.report["wheel"]["sha256"]:
            raise RuntimeError("Wheel hash differs from public PyPI metadata")
        # Match installed distribution files against the downloaded public wheel.
        import zipfile

        dist = metadata.distribution("pyobfus")
        with zipfile.ZipFile(wheel) as archive:
            for name in archive.namelist():
                if name.endswith("/") or ".dist-info/RECORD" in name:
                    continue
                installed = Path(dist.locate_file(name))
                if not installed.is_file() or installed.read_bytes() != archive.read(name):
                    raise RuntimeError("Installed wheel differs from public wheel")
        env["nuitka"] = self.run([sys.executable, "-m", "nuitka", "--version"]).stdout.strip()
        env["compiler"] = "pending actual Nuitka report in D5"

    def behavior(self, root: Path, frozen: bool = False) -> str:
        entry = [root / "main.exe"] if frozen else [sys.executable, "-B", root / "main.py"]
        normal = self.run([*entry, "pro"], cwd=root, consumer=frozen)
        if self.baseline and normal.stdout != self.baseline:
            raise RuntimeError("Normal output differs from source baseline")
        if normal.stdout.splitlines() != ["pricing-v1", "pro: 65.88"]:
            raise RuntimeError("Unexpected normal output")
        negative = self.run([*entry, "bogus_tier"], cwd=root, expected=None, consumer=frozen)
        if (
            negative.returncode == 0
            or "ValueError: Unknown pricing tier: bogus_tier" not in negative.stderr
        ):
            raise RuntimeError("Business negative failed")
        variant = Path(tempfile.mkdtemp(prefix="missing-", dir=self.work)) / root.name
        shutil.copytree(root, variant)
        labels = list(variant.rglob("label.txt"))
        if not labels:
            raise RuntimeError("Resource absent before negative test")
        for label in labels:
            label.unlink()
        missing_entry = (
            [variant / "main.exe"] if frozen else [sys.executable, "-B", variant / "main.py"]
        )
        missing = self.run([*missing_entry, "pro"], cwd=variant, expected=None, consumer=frozen)
        if missing.returncode == 0 or "FileNotFoundError" not in missing.stderr:
            raise RuntimeError("Resource negative failed")
        shutil.rmtree(variant.parent)
        return negative.stderr

    def d2(self) -> None:
        shutil.copytree(FIXTURE, self.source, ignore=shutil.ignore_patterns("__pycache__"))
        self.report["input_hashes"] = hashes(self.source)
        self.behavior(self.source)
        self.baseline = "pricing-v1\npro: 65.88\n"

    def d3(self) -> None:
        self.cli(
            self.source,
            "-o",
            self.protected,
            "--config",
            self.source / "pyobfus.yaml",
            "--save-mapping",
            self.private / "mapping.json",
            "--build-report",
            self.private / "build-report.json",
            "--provenance-manifest",
            self.private / "provenance.json",
            "--verify-syntax",
            "--jobs",
            "1",
            "--json",
        )
        shutil.copytree(
            self.source / "storefront/data", self.protected / "storefront/data", dirs_exist_ok=True
        )
        if list((self.work / "state").rglob("trial.json")) or list(
            (self.work / "state").rglob("license.json")
        ):
            raise RuntimeError("Unexpected Community licence/trial side effect")

    def restore(self, trace: str, name: str) -> bool:
        path = self.private / f"{name}-trace.txt"
        path.write_text(trace, encoding="utf-8")
        result = json.loads(
            self.cli(
                "--unmap", "--trace", path, "--mapping", self.private / "mapping.json", "--json"
            ).stdout
        )
        # Publish only known public function names actually present in restored output.
        public_names = sorted(
            set(
                re.findall(
                    r"def (\w+)\(",
                    "\n".join(p.read_text(encoding="utf-8") for p in FIXTURE.rglob("*.py")),
                )
            )
        )
        restored = result["unmapped_trace"]
        names = [n for n in public_names if re.search(r"in " + re.escape(n) + r"\b", restored)]
        statuses = [frame.get("status", "unknown") for frame in result.get("frames", [])]
        self.report[name + "_restoration"] = {
            "public_frame_names": names,
            "newly_restored_public_frame_names": [
                n for n in names if not re.search(r"in " + re.escape(n) + r"\b", trace)
            ],
            "frame_statuses": statuses,
            "unmatched_name_count": len(result.get("unmatched_names", [])),
            "scope": "Only frames emitted by this executable; removed frames cannot be recovered",
        }
        return "quote_order" in names

    def d4(self) -> None:
        if not self.restore(self.behavior(self.protected), "protected"):
            raise Unknown("No quote_order frame restored from protected source")

    def d5(self) -> None:
        if sys.platform != "win32":
            raise Blocked("Windows Nuitka toolchain unavailable on Linux; no compilation attempted")
        try:
            if metadata.version("nuitka") != "4.3.1":
                raise Blocked("Nuitka version mismatch")
        except metadata.PackageNotFoundError:
            raise Blocked("Nuitka unavailable") from None
        help_text = self.run([sys.executable, "-m", "nuitka", "--help"]).stdout
        for option in (
            "--mode",
            "--include-module",
            "--include-data-files",
            "--msvc",
            "--output-filename",
        ):
            if option not in help_text:
                raise Blocked("Locked Nuitka CLI lacks required option")
        for lane, root in (("original", self.source), ("protected", self.protected)):
            output = self.work / "build" / lane
            report = self.private / f"nuitka-{lane}.xml"
            try:
                self.run(
                    [
                        sys.executable,
                        "-m",
                        "nuitka",
                        "--mode=standalone",
                        "--msvc=latest",
                        "--assume-yes-for-downloads",
                        "--output-filename=main.exe",
                        f"--output-dir={output}",
                        f"--report={report}",
                        f"--include-data-files={root / 'storefront/data/label.txt'}=storefront/data/label.txt",
                        "--include-module=storefront.plugins.standard",
                        root / "main.py",
                    ],
                    cwd=root,
                    build=True,
                )
                self.behavior(output / "main.dist", frozen=True)
            except (RuntimeError, Blocked):
                self.report["build_failure_classification"] = (
                    "toolchain/fixture"
                    if lane == "original"
                    else "protected build; compare passing original control"
                )
                raise
            tree = ET.parse(report)
            compilers = [
                dict(node.attrib) for node in tree.iter() if "compiler" in node.tag.lower()
            ]
            self.report["environment"][lane + "_compiler_report"] = compilers
            if not compilers or not any(
                "version" in key.lower() for compiler in compilers for key in compiler
            ):
                raise Unknown("Actual compiler unavailable from Nuitka report")
        self.report["environment"][
            "compiler"
        ] = "Actual compiler attributes recorded from Nuitka XML (selector --msvc=latest)"
        self.report["download_consent"] = (
            "--assume-yes-for-downloads permits Windows dependency walker download; no interactive prompt"
        )

    def d6(self) -> None:
        shutil.copytree(self.work / "build/protected/main.dist", self.delivery)
        shutil.copytree(self.delivery, self.consumer)
        for name in ("source", "protected", "build"):
            (self.work / name).rename(self.work / (name + "-hidden"))

    def d7(self) -> None:
        self.frozen_trace = self.behavior(self.consumer, frozen=True)

    def d8(self) -> None:
        if not self.restore(self.frozen_trace, "frozen"):
            raise Unknown("Frozen trace does not restore quote_order; no fabricated frames")

    def d9(self) -> None:
        self.report["delivery_hashes"] = hashes(self.delivery)
        violations = audit_delivery(self.delivery, self.private, self.work / "source-hidden")
        self.report["delivery_violations"] = violations
        result = self.cli(
            "--check-delivery",
            self.delivery,
            "--build-report",
            self.private / "build-report.json",
            "--provenance-manifest",
            self.private / "provenance.json",
            "--json",
            expected=None,
        )
        checked = json.loads(result.stdout)
        # Preserve checker status/findings verbatim; sanitizer rejects unsafe payloads.
        self.report["delivery_check"] = {
            "status": checked["status"],
            "findings": checked.get("findings", []),
            "exit_code": result.returncode,
        }
        if violations or result.returncode != 0:
            raise RuntimeError("Delivery audit failed")
        if checked["status"] != "ok" or checked.get("findings"):
            raise Unknown("Checker findings retained verbatim; frozen internals not proven clean")

    def execute(self) -> int:
        dependencies = {
            "D2": [],
            "D3": ["D2"],
            "D4": ["D3"],
            "D5": ["D4"],
            "D6": ["D5"],
            "D7": ["D6"],
            "D8": ["D7"],
            "D9": ["D6"],
        }
        for number in range(1, 10):
            name = f"D{number}"
            start = time.monotonic()
            status, reason = "pass", "Executed successfully"
            try:
                deps = dependencies.get(name, [])
                if sys.platform == "win32" and number > 1:
                    deps = ["D1", *deps]
                if any(self.report["steps"][d]["status"] != "pass" for d in deps):
                    raise Blocked("Required prior step did not pass")
                getattr(self, name.lower())()
            except Blocked as exc:
                status, reason = "blocked", str(exc)
            except Unknown as exc:
                status, reason = "unknown", str(exc)
            except Exception as exc:
                status, reason = "fail", f"{type(exc).__name__}: consult private command logs"
            self.report["steps"][name] = {
                "status": status,
                "reason": reason,
                "seconds": round(time.monotonic() - start, 3),
            }
        self.report["private_hashes"] = hashes(self.private)
        self.report["build_seconds"] = round(self.build_seconds, 3)
        self.report["diagnostic_seconds"] = round(self.diagnostic_seconds, 3)
        start = time.monotonic()
        stages = {
            "A": self.report["steps"]["D2"]["status"],
            "B": aggregate({d: self.report["steps"][d]["status"] for d in ("D3", "D4", "D8")}),
            "C": "blocked",
            "E": aggregate(
                {d: self.report["steps"][d]["status"] for d in ("D1", "D5", "D6", "D7")}
            ),
            "F": self.report["steps"]["D9"]["status"],
            "G": "pass",
        }
        self.report["stages"] = stages
        self.report["status"] = aggregate(stages)
        safe_evidence(self.report)
        self.evidence.mkdir(parents=True, exist_ok=False)
        self.report["steps"]["D10"] = {
            "status": "pass",
            "reason": "Sanitized evidence serialized",
            "seconds": round(time.monotonic() - start, 3),
        }
        (self.evidence / "summary.json").write_text(
            json.dumps(self.report, indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            "# Windows Nuitka acceptance",
            "",
            f"Result: **{self.report['status']}**",
            "",
            f"Local smoke: {self.report['local_smoke']}",
            "",
            "| Step | Result | Reason | Seconds |",
            "|---|---|---|---|",
        ]
        lines += [
            f"| {k} | {v['status']} | {v['reason']} | {v['seconds']} |"
            for k, v in self.report["steps"].items()
        ]
        lines += [
            "",
            "Stages: " + ", ".join(f"{k}={v}" for k, v in stages.items()),
            "",
            *self.report["limitations"],
            "",
            "See summary.json for environment, commands, timings and hashes. Private diagnostics are not uploaded.",
        ]
        public_details = {
            key: self.report[key]
            for key in (
                "environment",
                "wheel",
                "protected_restoration",
                "frozen_restoration",
                "delivery_check",
                "delivery_violations",
                "build_failure_classification",
                "build_seconds",
                "diagnostic_seconds",
            )
            if key in self.report
        }
        lines += ["", "```json", json.dumps(public_details, indent=2), "```"]
        (self.evidence / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Exit 0 means the run executed without a failed or blocked required stage;
        # "partial" (honest unknowns such as uninspected frozen internals) stays the
        # recorded overall status in the evidence and is never reported as pass.
        return 0 if self.report["status"] in ("pass", "partial") else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, help="New private staging directory")
    parser.add_argument("--evidence-dir", type=Path, default=Path("evidence"))
    args = parser.parse_args()
    work = args.work_dir or Path(tempfile.mkdtemp(prefix="nuitka-acceptance-")) / "run"
    evidence = args.evidence_dir.resolve()
    work = work.resolve()
    if evidence == work or work in evidence.parents or evidence in work.parents:
        parser.error("Evidence must be separate from private staging")
    sys.exit(Runner(work, evidence).execute())


if __name__ == "__main__":
    main()

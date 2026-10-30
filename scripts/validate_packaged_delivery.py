"""Opt-in local PyInstaller acceptance using the executing Python's pyobfus.

Run with an isolated public-wheel interpreter or the repository venv. This
does not install tools, change CI, access real trial state, or publish artifacts.
L3 starts a local-only trial in the new work directory. Reports contain no key.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
from typing import Any

FIXTURE = Path(__file__).resolve().parents[1] / "integration_tests/packaging/multimodule"


def validate(work: Path, l3: bool) -> dict[str, Any]:
    work.mkdir(parents=True, exist_ok=False)
    home = work / "home"
    home.mkdir()
    private = work / "private"
    private.mkdir()
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    env["PYINSTALLER_CONFIG_DIR"] = str(work / "cache")
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    key = base64.b64encode(secrets.token_bytes(32)).decode()
    env.pop("PYOBFUS_VALIDATION_KEY", None)
    if l3:
        env["PYOBFUS_VALIDATION_KEY"] = key
    events = []

    def run(args, cwd=work, expected=0, run_env=None):
        started = time.monotonic()
        result = subprocess.run(
            [str(a) for a in args],
            cwd=cwd,
            env=env if run_env is None else run_env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        events.append(
            {
                "command": [str(a).replace(str(work), "<work>") for a in args],
                "exit_code": result.returncode,
                "seconds": round(time.monotonic() - started, 3),
            }
        )
        (private / f"step-{len(events):02d}.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        if result.returncode != expected:
            raise RuntimeError(
                f"step {len(events)} exited {result.returncode}, expected {expected}: {result.stderr[-2000:]}"
            )
        return result

    report: dict[str, Any] = {
        "python": sys.version,
        "pyobfus": version("pyobfus"),
        "runtime": version("pyobfus-runtime"),
        "pyinstaller": version("pyinstaller"),
        "pyinstaller_hooks_contrib": version("pyinstaller-hooks-contrib"),
        "cryptography": version("cryptography"),
        "cffi": version("cffi"),
        "platform": sys.platform,
        "l3": l3,
        "status": "running",
        "steps": events,
        "artifacts": [],
    }
    try:
        source = work / "src"
        shutil.copytree(FIXTURE, source, ignore=shutil.ignore_patterns("__pycache__", "README.md"))
        # A resource next to the entry script must survive both frozen modes.
        entry = source / "main.py"
        entry.write_text(
            entry.read_text()
            + "\nfrom pathlib import Path\nprint((Path(__file__).parent / 'data' / 'label.txt').read_text().strip())\n"
        )
        (source / "data").mkdir()
        (source / "data/label.txt").write_text("pricing-v1\n")
        report["input_sha256"] = {
            file.relative_to(source).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
            for file in sorted(source.rglob("*"))
            if file.is_file()
        }
        baseline = run([sys.executable, "-B", "main.py", "pro"], cwd=source).stdout
        run([sys.executable, "-B", "main.py", "bogus_tier"], cwd=source, expected=1)
        output = work / "protected"
        mapping = private / "mapping.json"
        build_report = private / "build.json"
        command = [
            sys.executable,
            "-m",
            "pyobfus",
            str(source),
            "-o",
            str(output),
            "--save-mapping",
            str(mapping),
            "--build-report",
            str(build_report),
            "--verify-syntax",
            "--jobs",
            "1",
            "--json",
        ]
        if l3:
            run(
                [
                    sys.executable,
                    "-c",
                    "from pyobfus.trial import start_trial; r=start_trial(); assert r['success'], r",
                ]
            )
            rules = private / "opacity.toml"
            rules.write_text(
                '[[rules]]\npattern="storefront.checkout.quote_order"\nlayer="encrypted"\n'
            )
            command += [
                "--level",
                "pro",
                "--crossfile-opacity",
                "--opacity-config",
                str(rules),
                "--bind-key-env",
                "PYOBFUS_VALIDATION_KEY",
            ]
        run(command)
        shutil.copytree(source / "data", output / "data")
        assert run([sys.executable, "-B", "main.py", "pro"], cwd=output).stdout == baseline
        executables = []
        for mode in ("onedir", "onefile"):
            dist = work / f"dist-{mode}"
            run(
                [
                    sys.executable,
                    "-m",
                    "PyInstaller",
                    f"--{mode}",
                    "--clean",
                    "--noconfirm",
                    "--name",
                    "storefront_app",
                    "--distpath",
                    dist,
                    "--workpath",
                    work / f"build-{mode}",
                    "--specpath",
                    private,
                    "--add-data",
                    f"{output / 'data'}{os.pathsep}data",
                    output / "main.py",
                ]
            )
            binary = dist / "storefront_app"
            if mode == "onedir":
                binary /= "storefront_app"
            if sys.platform == "win32":
                binary = binary.with_suffix(".exe")
            executables.append((mode, binary))
        # Frozen runs cannot fall back to either input tree or the builder's cwd.
        source.rename(work / "source-hidden")
        output.rename(work / "protected-hidden")
        target = work / "target"
        target.mkdir()
        for mode, binary in executables:
            target_env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.defpath}
            if l3:
                target_env["PYOBFUS_VALIDATION_KEY"] = key
            assert run([binary, "pro"], cwd=target, run_env=target_env).stdout == baseline
            crash = run([binary, "bogus_tier"], cwd=target, run_env=target_env, expected=1)
            assert "Unknown pricing tier" in crash.stderr
            trace = private / f"{mode}-trace.txt"
            trace.write_text(crash.stderr)
            restored = json.loads(
                run(
                    [
                        sys.executable,
                        "-m",
                        "pyobfus",
                        "--unmap",
                        "--trace",
                        trace,
                        "--mapping",
                        mapping,
                        "--json",
                    ]
                ).stdout
            )
            assert "quote_order" in restored["unmapped_trace"]
            assert restored["unmatched_names"] == []
            if l3:
                assert any(f["status"] == "name_only" for f in restored["frames"])
                missing_env = dict(target_env)
                missing_env.pop("PYOBFUS_VALIDATION_KEY")
                missing = run([binary, "pro"], cwd=target, run_env=missing_env, expected=1)
                assert "LicenseBindingError" in missing.stderr
                wrong_env = {
                    **target_env,
                    "PYOBFUS_VALIDATION_KEY": base64.b64encode(b"x" * 32).decode(),
                }
                wrong = run([binary, "pro"], cwd=target, run_env=wrong_env, expected=1)
                assert "OpacityRuntimeError" in wrong.stderr
            # Inspect our own newly built archive; never unmarshal arbitrary input.
            from PyInstaller.archive.readers import CArchiveReader

            archive = CArchiveReader(str(binary))
            pyz = archive.open_embedded_archive("PYZ.pyz")
            names = list(archive.toc) + list(pyz.toc)
            assert not any(
                "mapping" in n.lower()
                or "pyobfus_pro" in n
                or n == "pyobfus"
                or n.startswith("pyobfus.")
                for n in names
            )
            data = binary.read_bytes()
            assert key.encode() not in data and base64.b64decode(key) not in data
            assert not list(binary.parent.rglob("*mapping*.json"))
            checked = json.loads(
                run([sys.executable, "-m", "pyobfus", "--check-delivery", binary, "--json"]).stdout
            )
            assert checked["status"] == "warn"
            assert any(f["code"] == "delivery.frozen_uninspected" for f in checked["findings"])
            report["artifacts"].append(
                {
                    "mode": mode,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                    "result": "passed",
                    "archive_entries": len(names),
                    "traceback": "name_only encrypted frames" if l3 else "source mapping",
                }
            )
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc).replace(str(work), "<work>")
        raise
    finally:
        (work / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir", type=Path, required=True, help="New directory; never reuse a prior run"
    )
    parser.add_argument(
        "--l3", action="store_true", help="Exercise Pro L3 with an isolated local trial"
    )
    args = parser.parse_args()
    result = validate(args.work_dir.resolve(), args.l3)
    print(json.dumps({"status": result["status"], "artifacts": result["artifacts"]}, indent=2))


if __name__ == "__main__":
    main()

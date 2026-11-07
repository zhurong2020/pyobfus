# pre-commit hooks

Available since **0.13.0** in Community. These local
correctness and safety checks need no Pro licence. Inspection reads files;
it does not execute them, contact the network or consult licence state.
[pre-commit](https://pre-commit.com/) installs the hook environment separately
and may need network access during installation.

## Configure the hooks

Add this to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/zhurong2020/pyobfus
    rev: v0.13.0
    hooks:
      - id: pyobfus-no-private-material
      - id: pyobfus-check-delivery
        args: [dist/]
```

Use `v0.13.0` or a later release tag; 0.12.0 and earlier do not include the hooks.

Install pre-commit in your development environment, then enable both stages:

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

`pyobfus-no-private-material` checks the staged filenames supplied by
pre-commit, across all file types. It blocks recognized pyobfus mappings and
private-key files. It prints paths and reasons, never inspected contents.
Missing paths (deleted files), directories (including submodules), symlinks and
other nonregular files are silently skipped. Links are not followed, and the
module does not recursively scan arguments.

`pyobfus-check-delivery` runs `pyobfus --check-delivery` before pushing, and
can also run manually. It always runs without staged filenames: **set
`args: [<output dir>]`**, for example `args: [dist/]`. A missing output directory
exits **2**: build that output first, or set
`stages: [manual]` to run this hook only on demand.
It inspects built output for delivery mistakes, including mappings and keys;
additional build evidence can be supplied through the existing CLI options.

```bash
pre-commit run pyobfus-check-delivery --hook-stage manual
python -m pyobfus.precommit --json mapping.json other-file.pem
```

## Results and limits

The filename hook exits **0** for clean, **1** for findings, and **2** for
usage or read/permission errors on regular files. Errors take
precedence over findings. No filenames is a clean no-op. Use `--` before
filenames beginning with a dash.

`--json` emits one envelope with `version: 1`, `status` (`clean`, `findings`,
`error`), `findings` (each with `path`, `kind`, `message`) and `ai_hint`.
Finding kinds are `mapping` and `private_key`. An error means inspection is
incomplete, even if the findings array is empty.

The delivery hook retains the existing delivery CLI contract: 0 means ok or
warnings (review them), 1 means high findings, and 2 means incomplete inspection.

Detection reuses the delivery checker: mappings must have a `.json` suffix,
fit within 20 MiB and match its pyobfus mapping shape. Private keys are detected
by a PEM-style header at the start of the file (after whitespace), or the
reserved `.scrub.key.pem` suffix. Embedded keys later in a file, arbitrary
credentials, renamed non-JSON mappings and archive contents are not detected
by the filename hook. Only JSON files of at most 20 MiB are read fully for
mapping detection. Private-key detection reads only the first **64 KiB** of each
regular file; a key preceded by more leading whitespace than that head size is
not detected (unless its filename has the reserved suffix). Large files are
not errors and still receive the key-head check. There is no aggregate byte
budget or filename-count limit.

This is **not a general secret scanner**. Use gitleaks or detect-secrets
alongside it. A clean result is not proof of safety. Keep mappings and keys
outside both version control and delivered artifacts; rotate real credentials
that have already been committed or shipped.

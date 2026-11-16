# upload-artifact v7.0.2 review — 2026-11-16

Scope: [PR #241](https://github.com/zhurong2020/pyobfus/pull/241), head
`72623d75e85d0c489a50ca639c9101d143a3d0a9`. Review only; no merge or dispatch.

## Conclusion

No blocking compatibility defect found in the five changed upload steps. The
upgrade is suitable for these GitHub-hosted workflows, with the execution limits
below. A stale Windows workflow comment still says v4.6.2; updating it is a
non-blocking documentation correction. Merge remains a maintainer decision.

The PR title overstates its scope: Dogfood (three steps) and Draft PDF already use
v7 on main; those references change to v7.0.2. Only Windows Nuitka acceptance
changes from the fixed v4.6.2 SHA to fixed v7.0.2 SHA
`cf430e030ddbb5b0abf93d22962f4752f3646cd9`.

## Official-source compatibility review

- [v7.0.2 release](https://github.com/actions/upload-artifact/releases/tag/v7.0.2)
  resolves to that commit; hosted job logs independently resolve v7.0.2 to the same
  complete SHA.
- [v6 release](https://github.com/actions/upload-artifact/releases/tag/v6.0.0)
  requires Node 24 and Actions Runner >=2.327.1. Hosted Ubuntu job logs show
  runner 2.338.2. The repository uses hosted Ubuntu and windows-2022 for these
  steps; no self-hosted or GHES target was found.
- [v7 release](https://github.com/actions/upload-artifact/releases/tag/v7.0.0)
  introduces ESM and opt-in direct single-file upload. None of the five steps
  sets `archive: false`, so the new single-file restriction and ignored `name`
  behavior do not apply.
- [Pinned action.yml](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/action.yml)
  retains archive=true, hidden-files=false, overwrite=false, compression=6.
  Named artifacts are distinct; no shared-name multi-job append is used.
  Dogfood and Windows retention remains 14 days; PDF uses repository default.
- [Pinned README](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/README.md)
  confirms GHES unsupported for v4+, immutable artifacts, and common-root
  preservation for multiple paths. Canary's lane_b/lane_d retain their layout;
  Windows still uploads only sanitized `evidence/`; PDF remains a zipped paper
  artifact. File permission preservation is not required by these evidence files.

## Repository consumers and hosted evidence

`rg` across `.github`, `scripts`, and `docs` found the five upload steps in three
workflows, no `actions/download-artifact` usage and no artifact-id/output consumer.
Packaging validation does not depend on any of these uploaded artifacts; Lane C
uploads its verification evidence only. Human downloads use the run artifact UI.
No downstream automated download/extraction step exists to exercise in this PR.

[Dogfood run 43765286482](https://github.com/zhurong2020/pyobfus/actions/runs/43765286482):

| Job | Evidence |
| --- | --- |
| Lane A, job 132968882901 | Upload ran, 4 files, finalized artifact 14181908047, 20,795 bytes |
| Lanes B+D, job 132968883103 | Upload ran, 4 files, finalized artifact 14181354974, 3,472 bytes |
| Lane C | Skipped by its schedule/manual-only condition |

Artifact API confirms both are unexpired and expire on 2026-11-29, matching
14-day retention. Logs show archive=true and expected defaults. CI run
43765286483 and CodeQL run 43765286466 succeeded on this PR revision.

Draft PDF ran on the branch push, not the pull_request event: [run 43765279318](https://github.com/zhurong2020/pyobfus/actions/runs/43765279318),
job 132968859902. Logs resolve v7.0.2 to the expected SHA, show archive=true, and
finalize artifact `paper` / 14182480256 (140,364 bytes). The artifact API confirms
its default 90-day retention. The PR reports MERGEABLE / CLEAN at review time.

Windows Nuitka acceptance did not run on this revision; Lane C was skipped.
This review does not claim Windows upload or Lane C was newly tested. Rebuilding
the full Nuitka delivery merely to validate an unchanged upload contract was not
performed.

## Independent download verification

Downloaded all three existing ZIP artifacts through the GitHub API into memory
without extraction or execution. SHA-256 matched the API digest and `ZipFile.testzip()`
passed for each. Lane A contains four JSON/SARIF files at its root; canary retains
`lane_b/` and `lane_d/` with four evidence files; paper contains `paper.pdf`.
This validates download and archive layout for the three executed uploads.

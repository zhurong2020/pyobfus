# pyobfus vs browser-based obfuscators

Browser-based obfuscators are free, instant, and require you to paste your
source into someone else's web page. That last property is the whole
comparison.

A growing set of sites obfuscate Python in the browser: paste or upload a file,
get transformed source back, no install and no cost. Some now publish their own
comparison pages against PyArmor, Nuitka and Cython, so they show up on the
same searches this document does.

They are a real option for a single throwaway script. The difference that
decides most other cases is structural, not a feature gap:

| | Browser service | pyobfus |
|---|---|---|
| Where the source goes | Uploaded to a third party | Never leaves the machine |
| Scope | Typically one file at a time | Project-wide, scope-aware across modules |
| Repeatability | Manual, per visit | Config file, CLI, CI, GitHub Action |
| Debugging shipped code | No mapping returned | Reverse stack-trace mapping via `--unmap` |
| Build evidence | None | Provenance manifest, build report, reproducible output bytes |
| Inspectability | Server-side, not auditable | Apache-2.0 source, published attestations |

The upload is the part worth pausing on. Obfuscation is usually applied to code
someone considers worth protecting, and sending exactly that code to a third
party inverts the goal. Where the code belongs to an employer or client, or is
covered by a contract or regulation, "the source was uploaded to a website" is
often the answer that ends the discussion, independent of what the service does
with it afterwards. This document makes no claim about any particular service's
retention or handling; the point is that a local tool removes the question.

pyobfus obfuscates locally: the transformation itself makes no network call,
and the only outbound request anywhere in the package is the PyPI lookup in
`--check`'s dependency-hallucination advisory, which `--offline` disables. That
is verifiable rather than promised, because the source is Apache-2.0 and the
published artifacts carry PEP 740 attestations. Your code is never uploaded
either way.

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.

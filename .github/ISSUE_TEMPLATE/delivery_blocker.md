---
name: Delivery blocker / frozen format
about: Report a real delivery blocker or a gap in frozen-format inspection
title: '[DELIVERY] '
labels: [delivery-blocker]
assignees: ''
---

Never paste licence keys, private keys, mapping files or proprietary source.
Remove secrets, customer/payment details and personal data (including private
paths) from all examples, reports and attachments. Use a minimal synthetic
reproduction.

## Environment

- **Target Platform**: (OS, version and architecture)
- **Python Version**: (exact version; state whether it is free-threaded)
- **Freezer / Packager and Exact Version**: (PyInstaller, Nuitka, cx_Freeze,
  Briefcase, wheel/zip, etc.; include build mode such as onedir or onefile)
- **Build Platform**: (OS, version and architecture, if different from target)
- **pyobfus Version**:
- **Edition**: (Community or Pro; do not include any licence key)

## Delivery Blocker

Describe what blocks delivery and the expected and actual behavior. For example:

- Behavior differs between the original and protected/packaged application.
- A traceback cannot be restored.
- A delivery-check gap leaves a format or payload uninspected.
- A resource needs protection or a raw asset is exposed.
- An L3 coverage gap leaves a method or nested function unprotected.

## Minimal Reproduction or Report Excerpt

Provide a minimal synthetic reproduction with the directory tree, exact build
commands/configuration and steps to reproduce, or a relevant excerpt from
`--check-delivery --json` or the build report with secrets removed. Include
output, exit status and exception type when relevant; review excerpts for
private paths and other sensitive data before posting.

The [delivery reference application](https://github.com/zhurong2020/pyobfus/tree/main/examples/delivery_reference)
is the shared reproduction baseline. Reproduce against it when possible and
describe any minimal changes needed.

```text
# Minimal reproduction steps or sanitized report excerpt
```

## Shipping Impact

Does this block shipping to customers now? (Yes / No)

Describe the technical impact and any workaround. Do not identify customers or
include payment information, private support history or proprietary source.

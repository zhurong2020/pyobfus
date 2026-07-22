# Show HN submission

> **NOT PUBLISHABLE COPY.** Hacker News prohibits generated or AI-edited text.
> This file is only a factual and operational checklist. The maintainer must
> independently write the title, submission text, first comment, and replies.

Current Show HN rules require something people can run. Submit only after
normal community participation and when the maintainer is available to answer
questions for the first 90 minutes. There is no documented public account-age
or karma threshold to optimize for.

## Submission facts

These are facts to verify before the maintainer writes the submission; they are
not sentences to paste into HN.

- The title must begin with `Show HN`.
- Submit the runnable project, not the DEV article:
  <https://github.com/zhurong2020/pyobfus>
- Zero-install and normal install paths must work from public instructions.
- The maintainer must be available to discuss the project after submission.
- Do not ask anyone to vote or comment.

## Maintainer-only authoring checklist

The maintainer should decide, from personal experience, which facts belong in
the submission and express them without AI drafting or editing:

- Personal reason for building pyobfus.
- Apache-2.0 Core and source-separated commercial Pro.
- AST transformation plus a locally held reverse mapping for crash traces.
- Framework-aware preservation for reflective Python frameworks.
- Separate `pyobfus-mcp` package with eight executable tools.
- Public quick start: `pip install pyobfus` followed by the real CLI syntax.
- Version 0.5.4 device-binds each Pro String Vault key.
- Release evidence: 1,046 passing Core tests, one skip, Python 3.9–3.14.
- Threat-model boundary: obfuscation raises analysis cost; a runtime-controlling
  attacker can still use dynamic analysis or extract material from memory.
- Feedback sought: broken frameworks, mapping friction, and threat-model errors.

## Response principles

- Every response must be independently written by the maintainer.
- Do not describe AST obfuscation as irreversible security.
- State that Pro is commercial and source-separated when relevant.
- For trial-bypass questions, link SECURITY.md and say the local trial is a
  convenience control, not a security boundary.
- Do not ask for votes or coordinate comments.

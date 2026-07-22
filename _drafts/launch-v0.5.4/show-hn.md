# Show HN submission

Current Show HN rules require something people can run and currently restrict
accounts that are not yet familiar with the community. Submit only when the
maintainer account is eligible and available to answer questions.

## Title and URL

```text
Show HN: Pyobfus – Obfuscate Python without losing readable crash traces
https://github.com/zhurong2020/pyobfus
```

## First comment

Author here. I built pyobfus around a problem I had not seen other Python
obfuscators treat as a first-class constraint: production code can be hard to
read without making its crash reports useless to the developer and their coding
assistant.

The Apache-2.0 core mangles the AST, understands common framework reflection
points, and writes a mapping that can reverse an obfuscated traceback locally.
There is also an MCP server, so the preflight/config/obfuscate/unmap flow can be
called by Claude Code, Cursor, and other agents without scraping terminal text.

Version 0.5.4 also device-binds each Pro String Vault key. The honest boundary:
core obfuscation raises the cost of casual inspection; even encrypted wrappers
do not stop an attacker who controls a running process and can dump memory.

Quick try:

```text
pip install pyobfus
pyobfus --check src/ --json
pyobfus src/ -o dist/ --save-mapping mapping.json
```

The current release has 1,046 passing core tests across Python 3.9–3.14. I
would value hard questions about the threat model, broken frameworks, or the
mapping workflow more than feature applause.

## Response principles

- Do not describe AST obfuscation as irreversible security.
- State that Pro is commercial and source-separated when relevant.
- For trial-bypass questions, link SECURITY.md and say the local trial is a
  convenience control, not a security boundary.
- Do not ask for votes or coordinate comments.

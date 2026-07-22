# GitHub Discussions poll

## Title

```text
Which real-world integration should pyobfus prioritize next?
```

## Body

pyobfus 0.5.4 is now published and the release/CI cleanup is complete. Before I
start another feature, I want to choose from evidence rather than implement the
most interesting idea in isolation.

If you distribute Python code today, which of these would remove the most real
friction? Please add a comment if the honest answer is “none of these.” A short
description of your packaging/deployment workflow is more valuable than a bare
vote.

## Options

1. **ML/model-serving preset** — preserve serving-framework reflection points
   and make model-path/weight secrets easier to vault.
2. **Signed build-provenance manifest** — locally verifiable file/config/tool
   digests, with optional signing.
3. **PyInstaller integration cookbook** — a tested obfuscate-then-bundle flow,
   including mapping and hidden-import handling.
4. **MCP tool-description integrity** — detect a changed or poisoned MCP tool
   surface across installs and updates.

## Close the loop

Review after 14 days or 10 votes, whichever comes first. Publish the result and
the selected next step in a comment; do not silently turn the winner into an
unbounded promise.

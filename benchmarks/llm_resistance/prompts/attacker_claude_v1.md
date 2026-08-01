You are a reverse-engineering analyst. You are given a single Python module that
has been obfuscated. Recover its original behavior by STATIC ANALYSIS ONLY. This
session has no tool access (no file, shell, or network tools are available to
you) — do not attempt to inspect local files, run tools, or execute the
supplied module; reason over the text below only.

Return a clean, self-contained Python reimplementation that defines these
top-level functions with exactly these names and parameter counts:

{ENTRYPOINTS}

Match the original input/output behavior for every reachable input. If logic is
encrypted or absent from the artifact, make a best effort but do not invent
constants that are not visible.

Your final response must match the supplied JSON schema:

- `reimplementation`: raw Python source without Markdown fences.
- `explanation`: one to three sentences describing the recovered behavior.

--- OBFUSCATED MODULE ---
{OBFUSCATED}

"""Pluggable LLM attacker(s) for the resistance benchmark.

The ``Attacker`` interface is model-agnostic. Two implementations ship:

- ``StubAttacker``  -- deterministic, offline. Returns the obfuscated source
  unchanged. It "recovers" C0 (input == original) but fails C1+ (mangled names),
  which is exactly what proves the scorer discriminates. Use in CI / smoke runs.
- ``AnthropicAttacker`` -- the real analyst via the Anthropic API. Fixed model,
  temperature 0, a frozen prompt (``prompts/attacker_v1.md``) hashed into every
  result for reproducibility. Requires ``anthropic`` + ``ANTHROPIC_API_KEY``.
- ``CodexCliAttacker`` -- invokes ``codex exec`` with saved ChatGPT
  authentication. It deliberately removes API-key variables from the child
  environment so a run cannot silently switch from subscription usage to API
  billing.
- ``ClaudeCodeCliAttacker`` -- invokes ``claude -p`` with saved Claude
  subscription authentication (same env-stripping discipline as the Codex
  adapter) and ``--allowedTools ""`` so the session has no file/shell/network
  tool access at all -- the model can only reason over the prompt text, which
  is this benchmark's static-analysis threat model enforced at the tool layer,
  not just requested in the prompt.

See ``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_PROMPTS = Path(__file__).parent / "prompts"


@dataclass
class AttackResult:
    reimplementation: str
    explanation: str
    raw_response: str = ""


@dataclass
class Attacker:
    """Base attacker. Subclasses implement :meth:`deobfuscate`."""

    name: str = "base"

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
        raise NotImplementedError

    def descriptor(self) -> dict:
        """Reproducibility record stamped into results.json."""
        return {"attacker": self.name}


@dataclass
class StubAttacker(Attacker):
    name: str = "stub"

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
        # Echo the artifact back. On C0 this is the original (recovers); on C1+
        # the entrypoint names are mangled away (fails) -- the scorer must see
        # exactly this difference for the harness to be trustworthy.
        return AttackResult(
            reimplementation=obfuscated_src,
            explanation="(stub attacker: echoes the input, performs no analysis)",
            raw_response="",
        )


def _entrypoints_block(entrypoints: list[dict]) -> str:
    lines = []
    for ep in entrypoints:
        params = ", ".join(f"arg{i + 1}" for i in range(ep["arity"]))
        lines.append(f"- {ep['name']}({params})")
    return "\n".join(lines)


def _extract_code(response: str) -> tuple[str, str]:
    """Split a ```python fenced block (reimplementation) from trailing prose."""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
    if not m:
        return "", response.strip()
    code = m.group(1)
    explanation = (response[: m.start()] + response[m.end() :]).strip()
    return code, explanation


def _default_codex_command() -> tuple[str, ...]:
    """Return the installed Codex CLI command without invoking it."""
    candidates = ("codex.cmd", "codex") if os.name == "nt" else ("codex",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return (resolved,)
    raise RuntimeError("Codex CLI was not found; install @openai/codex and run `codex login`")


@dataclass
class CodexCliAttacker(Attacker):
    """Real attacker backed by ``codex exec`` and ChatGPT authentication.

    ``command`` is injectable so offline tests can use a fake CLI. Production
    runs leave it unset and discover the installed ``codex`` command.
    """

    name: str = "codex-cli"
    model: str = ""
    timeout: float = 600.0
    command: tuple[str, ...] | None = field(default=None, repr=False)
    _prompt_path: Path = field(default=_PROMPTS / "attacker_codex_v1.md", repr=False)
    _schema_path: Path = field(default=_PROMPTS / "attack_result.schema.json", repr=False)

    def _template(self) -> str:
        return self._prompt_path.read_text(encoding="utf-8")

    def _resolved_command(self) -> tuple[str, ...]:
        return self.command or _default_codex_command()

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
        if not self.model:
            raise ValueError("CodexCliAttacker requires an explicit model id")

        prompt = (
            self._template()
            .replace("{ENTRYPOINTS}", _entrypoints_block(entrypoints))
            .replace("{OBFUSCATED}", obfuscated_src)
        )
        env = os.environ.copy()
        # Subscription authentication is the point of this adapter. Never let
        # a developer shell's API key silently turn the measurement into a
        # billable API run.
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(key, None)

        with tempfile.TemporaryDirectory(prefix="pyobfus-codex-attacker-") as td:
            output_path = Path(td) / "attack-result.json"
            cmd = [
                *self._resolved_command(),
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--model",
                self.model,
                "-c",
                'model_reasoning_effort="low"',
                "--output-schema",
                str(self._schema_path.resolve()),
                "--output-last-message",
                str(output_path),
                "-",
            ]
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=td,
                env=env,
            )
            if proc.returncode != 0:
                detail = proc.stderr.strip().splitlines()[-1:] or ["no stderr"]
                raise RuntimeError(f"codex exec failed: {detail[0][:300]}")
            if not output_path.exists():
                raise RuntimeError("codex exec produced no structured output file")
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError("codex exec returned invalid structured output") from exc

        code = str(payload.get("reimplementation", ""))
        explanation = str(payload.get("explanation", ""))
        # Be tolerant if a model includes a fence despite the schema guidance.
        fenced_code, trailing = _extract_code(code)
        if fenced_code:
            code = fenced_code
            explanation = explanation or trailing
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return AttackResult(
            reimplementation=code,
            explanation=explanation,
            raw_response=raw,
        )

    def descriptor(self) -> dict:
        prompt_hash = hashlib.sha256(self._template().encode("utf-8")).hexdigest()[:16]
        command = self._resolved_command()
        try:
            proc = subprocess.run(
                [*command, "--version"], capture_output=True, text=True, timeout=15
            )
            cli_version = (proc.stdout or proc.stderr).strip().splitlines()[-1]
        except (OSError, subprocess.SubprocessError, IndexError):
            cli_version = "unknown"
        return {
            "attacker": self.name,
            "model": self.model,
            "reasoning_effort": "low",
            "auth": "saved ChatGPT login (API-key variables removed)",
            "codex_cli": cli_version,
            "prompt": self._prompt_path.name,
            "prompt_sha256_16": prompt_hash,
        }


def _default_claude_command() -> tuple[str, ...]:
    """Return the installed Claude Code CLI command without invoking it."""
    candidates = ("claude.cmd", "claude") if os.name == "nt" else ("claude",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return (resolved,)
    raise RuntimeError("Claude Code CLI was not found; install it and run `claude login`")


@dataclass
class ClaudeCodeCliAttacker(Attacker):
    """Real attacker backed by ``claude -p`` and saved Claude subscription auth.

    Mirrors :class:`CodexCliAttacker`'s discipline: strip API-key env vars so
    the run cannot silently switch from subscription usage to API billing,
    and constrain the session so it can only reason over the prompt text.
    Unlike the Codex CLI's ``--sandbox read-only``, Claude Code has no
    sandbox flag; the equivalent control here is ``--allowedTools ""``, which
    grants zero tools (no Bash/Read/Write/etc.), verified empirically to stop
    the model from touching the filesystem or attempting execution rather
    than merely asking it not to in the prompt.
    """

    name: str = "claude-code-cli"
    model: str = ""
    timeout: float = 600.0
    command: tuple[str, ...] | None = field(default=None, repr=False)
    _prompt_path: Path = field(default=_PROMPTS / "attacker_claude_v1.md", repr=False)
    _schema_path: Path = field(default=_PROMPTS / "attack_result.schema.json", repr=False)

    def _template(self) -> str:
        return self._prompt_path.read_text(encoding="utf-8")

    def _resolved_command(self) -> tuple[str, ...]:
        return self.command or _default_claude_command()

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
        if not self.model:
            raise ValueError("ClaudeCodeCliAttacker requires an explicit model id")

        prompt = (
            self._template()
            .replace("{ENTRYPOINTS}", _entrypoints_block(entrypoints))
            .replace("{OBFUSCATED}", obfuscated_src)
        )
        schema = self._schema_path.read_text(encoding="utf-8")
        env = os.environ.copy()
        # Subscription authentication is the point of this adapter. Never let
        # a developer shell's API key silently turn the measurement into a
        # billable API run.
        env.pop("ANTHROPIC_API_KEY", None)

        with tempfile.TemporaryDirectory(prefix="pyobfus-claude-attacker-") as td:
            cmd = [
                *self._resolved_command(),
                "-p",
                "--output-format",
                "json",
                "--json-schema",
                schema,
                "--model",
                self.model,
                "--allowedTools",
                "",
            ]
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=td,
                env=env,
            )
            if proc.returncode != 0:
                detail = proc.stderr.strip().splitlines()[-1:] or ["no stderr"]
                raise RuntimeError(f"claude -p failed: {detail[0][:300]}")
            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("claude -p returned invalid JSON on stdout") from exc

        if payload.get("is_error"):
            raise RuntimeError(f"claude -p reported an error: {payload.get('result', '')[:300]}")

        structured = payload.get("structured_output")
        if structured is None:
            # Fall back to parsing `result`, which --json-schema documents as
            # a JSON-encoded string mirroring structured_output.
            try:
                structured = json.loads(payload.get("result", ""))
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "claude -p produced no structured_output or parseable result"
                ) from exc

        code = str(structured.get("reimplementation", ""))
        explanation = str(structured.get("explanation", ""))
        fenced_code, trailing = _extract_code(code)
        if fenced_code:
            code = fenced_code
            explanation = explanation or trailing
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return AttackResult(reimplementation=code, explanation=explanation, raw_response=raw)

    def descriptor(self) -> dict:
        prompt_hash = hashlib.sha256(self._template().encode("utf-8")).hexdigest()[:16]
        command = self._resolved_command()
        try:
            proc = subprocess.run(
                [*command, "--version"], capture_output=True, text=True, timeout=15
            )
            cli_version = (proc.stdout or proc.stderr).strip().splitlines()[-1]
        except (OSError, subprocess.SubprocessError, IndexError):
            cli_version = "unknown"
        return {
            "attacker": self.name,
            "model": self.model,
            "auth": "saved Claude subscription login (API-key variables removed)",
            "tool_access": 'none (--allowedTools "")',
            "claude_cli": cli_version,
            "prompt": self._prompt_path.name,
            "prompt_sha256_16": prompt_hash,
        }


@dataclass
class AnthropicAttacker(Attacker):
    name: str = "anthropic"
    model: str = ""
    max_tokens: int = 4096
    _prompt_path: Path = field(default=_PROMPTS / "attacker_v1.md", repr=False)

    def _template(self) -> str:
        return self._prompt_path.read_text(encoding="utf-8")

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
        if not self.model:
            raise ValueError("AnthropicAttacker requires an explicit model id")
        import anthropic  # lazy: only needed for real runs

        prompt = (
            self._template()
            .replace("{ENTRYPOINTS}", _entrypoints_block(entrypoints))
            .replace("{OBFUSCATED}", obfuscated_src)
        )
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        code, explanation = _extract_code(text)
        return AttackResult(reimplementation=code, explanation=explanation, raw_response=text)

    def descriptor(self) -> dict:
        prompt_hash = hashlib.sha256(self._template().encode("utf-8")).hexdigest()[:16]
        return {
            "attacker": self.name,
            "model": self.model,
            "temperature": 0,
            "prompt": self._prompt_path.name,
            "prompt_sha256_16": prompt_hash,
        }


def make_anthropic_judge(model: str):
    """Return a ``(explanation, ground_truth) -> int 0..3`` judge callable."""
    template = (_PROMPTS / "judge_v1.md").read_text(encoding="utf-8")

    def judge(explanation: str, ground_truth: str) -> int:
        import anthropic

        client = anthropic.Anthropic()
        prompt = template.replace("{GROUND_TRUTH}", ground_truth).replace(
            "{EXPLANATION}", explanation
        )
        resp = client.messages.create(
            model=model,
            max_tokens=8,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        digits = re.findall(r"[0-3]", text)
        return int(digits[0]) if digits else 0

    return judge

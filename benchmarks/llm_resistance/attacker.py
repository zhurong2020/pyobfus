"""Pluggable LLM attacker(s) for the resistance benchmark.

The ``Attacker`` interface is model-agnostic. Two implementations ship:

- ``StubAttacker``  -- deterministic, offline. Returns the obfuscated source
  unchanged. It "recovers" C0 (input == original) but fails C1+ (mangled names),
  which is exactly what proves the scorer discriminates. Use in CI / smoke runs.
- ``AnthropicAttacker`` -- the real analyst via the Anthropic API. Fixed model,
  temperature 0, a frozen prompt (``prompts/attacker_v1.md``) hashed into every
  result for reproducibility. Requires ``anthropic`` + ``ANTHROPIC_API_KEY``.

See ``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import hashlib
import re
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


@dataclass
class AnthropicAttacker(Attacker):
    name: str = "anthropic"
    model: str = "claude-sonnet-5"
    max_tokens: int = 4096
    _prompt_path: Path = field(default=_PROMPTS / "attacker_v1.md", repr=False)

    def _template(self) -> str:
        return self._prompt_path.read_text(encoding="utf-8")

    def deobfuscate(self, obfuscated_src: str, entrypoints: list[dict]) -> AttackResult:
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


def make_anthropic_judge(model: str = "claude-sonnet-5"):
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

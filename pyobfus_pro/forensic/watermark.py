"""Forensic watermarking core: seed derivation + deterministic RNG.

The structural property we want from a watermark: **two builds for two
different buyers, of identical source, must differ in a way that uniquely
identifies the buyer; given any leaked artifact, we can compute which
buyer's build it derived from.**

Construction (W4 v1):

1. ``forensic_seed(buyer_id, assignment_hash) -> 32 bytes``
   SHA-256 over a versioned personalization string + buyer ID + the
   layer-assignment hash. Two builds with the same buyer ID + same source
   layout produce the same seed. Two buyers produce different seeds. Two
   different layer assignments (different opacity.toml) for the same buyer
   also produce different seeds -- which is correct, because the build
   artifact is genuinely different.

2. :class:`WatermarkRNG` -- HMAC-SHA256(seed, counter) counter-mode stream
   cipher. Byte-reproducible across processes, Python versions, OS, and
   architectures (HMAC + SHA-256 are wire-format-stable). Output is
   uniform-random per HMAC's PRF assumption. **Crucially NOT** ``random``
   /``hashlib.shake_256(...).digest(n)`` -- ``random`` has undefined
   reproducibility across versions, and shake's truncation semantics are
   correct but make the streaming-RNG-with-state pattern awkward. HMAC-CTR
   is the textbook deterministic-RNG construction for cryptographic use.

3. ``derive_layer_key(buyer_id, assignment_hash) -> 32 bytes``
   First 32 bytes of the buyer's RNG stream. Used as the AES-256 key for
   P2-1 L3 ciphertext + P2-11 vault constants. The build orchestrator
   passes this to ``opacity.transform_module(layer_key=...)`` and
   ``vault.transform_module(vault_keys=...)`` -- both already accept
   externally supplied keys (W3-B / W3-C).

4. ``verify_layer_key_match(suspect_source, candidate_buyer_id,
   original_assignment_hash) -> bool``
   Forensic recovery primitive. Re-derives the buyer's key, parses the
   suspect source for ``_LAYER_KEY = b"..."``, returns True on byte
   equality. Layer keys cannot be patched away without invalidating every
   ``_CIPHER_<name>`` constant in the build, so this is a high-confidence
   buyer attribution even when the leaker patched plaintext code (CLASP-
   style robustness, arXiv 2510.11251).

**Patent novelty (claim narrowing per the PATENT_NOTES P2-7 section)**:

- vmp-protector 1.0.0 ships ``--fingerprint`` but in bytecode-VM lane
  (different mechanism). pyobfus operates AST-level + emits pure Python.
- The shared seed driving BOTH the L3 layer key AND (eventually) Core's
  rename-map RNG AND dead-code injection RNG is the structural
  combination claim element. Single seed, multiple deterministic key
  derivations across multiple build passes. Prior art ships a single
  fingerprint into a single mechanism.
- The forensic recovery primitive's robustness derives from L3's
  cryptographic binding: the layer key cannot be patched in isolation
  without breaking decryption of every L3 function in the build, so
  attempts to "scrub the watermark" are detectable as broken artifacts.
"""

from __future__ import annotations

import hashlib
import hmac
import re

_PERSONALIZATION = b"pyobfus-v0.5-forensic-watermark-v1"
_SEED_SIZE = 32  # SHA-256 digest size; matches AES-256 key size
_HMAC_BLOCK_SIZE = 32  # SHA-256 digest size

_LAYER_KEY_LITERAL_RE = re.compile(
    r"^_LAYER_KEY = (b['\"][^\n]+)$",
    re.MULTILINE,
)


class WatermarkError(ValueError):
    """Raised on invalid forensic-watermark inputs."""


def forensic_seed(buyer_id: str, assignment_hash: bytes | bytearray) -> bytes:
    """Compute the 32-byte master seed for a buyer's deterministic build.

    Args:
        buyer_id: Non-empty UTF-8 string. The build orchestrator passes
            whatever identifier it uses (license-issuer customer ID,
            email, UUID -- any stable identifier).
        assignment_hash: 32-byte SHA-256 from
            :meth:`pyobfus_pro.opacity.OpacityConfig.assignment_hash`.
            Binds the seed to the specific layer-assignment shape of this
            source: a config change re-shuffles the watermark, but two
            builds with identical config + buyer ID are byte-identical.

    Returns:
        32-byte master seed. Feed to :class:`WatermarkRNG`.

    Raises:
        WatermarkError: on empty buyer_id, non-string buyer_id, or
            wrong-size assignment_hash.

    The construction is::

        sha256(_PERSONALIZATION || \\x00 || buyer_id_utf8 || \\x00 || assignment_hash)

    Personalization separates this seed from any other SHA-256 use of the
    same inputs -- a cryptographic best-practice (BIP-32, NIST SP 800-56C
    KDF-with-info pattern). The version tag ``v1`` lets us migrate without
    breaking historical artifact attribution: a future v2 with different
    construction is statically distinguishable.
    """
    if not isinstance(buyer_id, str):
        raise WatermarkError(f"buyer_id must be a string, got {type(buyer_id).__name__}")
    if not buyer_id:
        raise WatermarkError("buyer_id must be non-empty")
    if not isinstance(assignment_hash, (bytes, bytearray)) or len(assignment_hash) != _SEED_SIZE:
        raise WatermarkError(
            f"assignment_hash must be exactly {_SEED_SIZE} bytes "
            f"(sha256 from OpacityConfig.assignment_hash); got "
            f"{len(assignment_hash) if isinstance(assignment_hash, (bytes, bytearray)) else type(assignment_hash).__name__}"
        )
    h = hashlib.sha256()
    h.update(_PERSONALIZATION)
    h.update(b"\x00")
    h.update(buyer_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(bytes(assignment_hash))
    return h.digest()


class WatermarkRNG:
    """Deterministic byte-reproducible RNG for the watermarked-build path.

    HMAC-SHA256 counter-mode stream cipher: each 32-byte block is
    ``HMAC-SHA256(seed, counter.to_bytes(8, "big"))`` for an incrementing
    big-endian counter. Stateful: each :meth:`next_bytes` advances the
    counter. Two RNGs constructed from the same seed produce identical
    output streams.

    **Why not ``random.Random(seed)`` or ``hashlib.shake_256(seed).digest(n)``**:

    - ``random.Random`` is a Mersenne Twister with undocumented stability
      guarantees across Python releases. Output differs across CPython
      3.10/3.11/3.12 in some seeded paths. Unsuitable for forensic
      reproducibility years after a build.
    - ``hashlib.shake_256(...).digest(n)`` is byte-reproducible but doesn't
      support streaming with checkpoint/resume; you must re-hash the
      entire prefix to extract a later region. HMAC-CTR is naturally
      streaming.
    - ``Crypto.Random`` / ``cryptography.fernet`` have process-state /
      OS-entropy dependencies, not deterministic.

    HMAC-SHA256 with a fixed key + a counter is the same construction
    NIST SP 800-90A "HMAC_DRBG" uses for its block-generate primitive
    (different reseed semantics; for our deterministic-only use we don't
    need reseed). Cryptographic strength + byte-reproducible.
    """

    def __init__(self, seed: bytes | bytearray) -> None:
        if not isinstance(seed, (bytes, bytearray)) or len(seed) != _SEED_SIZE:
            raise WatermarkError(
                f"WatermarkRNG seed must be exactly {_SEED_SIZE} bytes; got "
                f"{len(seed) if isinstance(seed, (bytes, bytearray)) else type(seed).__name__}"
            )
        self._key = bytes(seed)
        self._counter = 0

    def next_bytes(self, n: int) -> bytes:
        """Return the next ``n`` bytes from the deterministic stream.

        Args:
            n: Number of bytes to return. Must be positive. The RNG
                generates 32-byte blocks internally and slices to ``n``.

        Returns:
            Exactly ``n`` bytes.

        Raises:
            WatermarkError: when ``n`` is not a positive integer.
        """
        if not isinstance(n, int) or n <= 0:
            raise WatermarkError(f"next_bytes(n) requires n > 0; got {n!r}")
        out = bytearray()
        while len(out) < n:
            self._counter += 1
            block = hmac.new(self._key, self._counter.to_bytes(8, "big"), "sha256").digest()
            out.extend(block)
        return bytes(out[:n])

    def randint(self, lo: int, hi: int) -> int:
        """Uniform integer in ``[lo, hi]`` (inclusive on both ends).

        Used by Core's rename-map / dead-code passes when integrated.
        Implementation uses rejection sampling over 8-byte blocks to avoid
        modulo bias.
        """
        if not isinstance(lo, int) or not isinstance(hi, int):
            raise WatermarkError("randint bounds must be ints")
        if lo > hi:
            raise WatermarkError(f"randint requires lo <= hi; got {lo} > {hi}")
        span = hi - lo + 1
        if span == 1:
            return lo
        # Reject samples in the upper "remainder" region to avoid modulo bias.
        threshold = (1 << 64) - ((1 << 64) % span)
        while True:
            raw = int.from_bytes(self.next_bytes(8), "big")
            if raw < threshold:
                return lo + (raw % span)


def derive_layer_key(buyer_id: str, assignment_hash: bytes | bytearray) -> bytes:
    """Derive the 32-byte AES-256 layer key for a buyer's build.

    Used by the build orchestrator to pre-compute the key that gets
    passed to :func:`pyobfus_pro.transformers.opacity.transform_module`
    via the ``layer_key=`` keyword and to
    :func:`pyobfus_pro.transformers.vault.transform_module` via
    ``vault_keys={...}``. Same key powers L3 ciphertext + Vault entries
    in the buyer's build, which means the buyer's "fingerprint" is
    cryptographically inseparable from the encrypted contents.

    Args:
        buyer_id: see :func:`forensic_seed`.
        assignment_hash: see :func:`forensic_seed`.

    Returns:
        32-byte AES-256 key. Same buyer + same assignment_hash always
        produces the same key.

    Raises:
        WatermarkError: see :func:`forensic_seed`.
    """
    seed = forensic_seed(buyer_id, assignment_hash)
    return WatermarkRNG(seed).next_bytes(32)


def verify_layer_key_match(
    suspect_source: str,
    candidate_buyer_id: str,
    original_assignment_hash: bytes | bytearray,
) -> bool:
    """Forensic recovery: does the suspect artifact derive from this buyer?

    Strategy: derive the candidate buyer's layer key, parse the suspect
    Python source for the ``_LAYER_KEY = b"..."`` literal, return True iff
    the bytes match exactly.

    Args:
        suspect_source: Python source text of the leaked / recovered
            obfuscated module. Must contain a top-level
            ``_LAYER_KEY = b"..."`` assignment (emitted by the opacity
            transformer for any module containing L3 functions).
        candidate_buyer_id: The buyer ID being tested.
        original_assignment_hash: The 32-byte
            :meth:`OpacityConfig.assignment_hash` value computed from the
            ORIGINAL source (the developer's build inputs), not from the
            suspect artifact -- the suspect's `assignment_hash` is not
            recoverable from output if rules were applied.

    Returns:
        True if the candidate buyer's derived key matches the suspect
        artifact's embedded ``_LAYER_KEY``. False otherwise (including
        when no ``_LAYER_KEY`` was found in the suspect source).

    Raises:
        WatermarkError: on invalid candidate_buyer_id /
            original_assignment_hash.

    **Robustness property**: the layer key is the cryptographic root of
    EVERY ``_CIPHER_<name>`` constant in the artifact. An attacker cannot
    swap the layer key constant alone -- doing so makes every L3 function
    in the artifact fail GCM tag verification, breaking the artifact at
    runtime. The watermark is therefore "tamper-evident" by virtue of L3's
    cryptographic structure, not via a separate signature mechanism. The
    patent claim language for this property is "watermark binding via
    cryptographic dependency chain" (TBD in P2-7 section claim drafting).
    """
    expected = derive_layer_key(candidate_buyer_id, original_assignment_hash)
    embedded = _extract_layer_key_constant(suspect_source)
    if embedded is None:
        return False
    return embedded == expected


def _extract_layer_key_constant(suspect_source: str) -> bytes | None:
    """Parse ``_LAYER_KEY = b"..."`` from a Python source string.

    Returns the bytes value, or None if no top-level ``_LAYER_KEY``
    bytes-literal assignment is found.

    Implementation note: this uses a regex match to locate the line, then
    Python's own ``ast.literal_eval`` for safe parsing of the bytes
    literal. A naive regex over the bytes-literal content would mis-handle
    embedded escapes; ``literal_eval`` is the right tool.
    """
    import ast

    match = _LAYER_KEY_LITERAL_RE.search(suspect_source)
    if match is None:
        return None
    literal_text = match.group(1)
    try:
        value = ast.literal_eval(literal_text)
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, bytes):
        return None
    return value

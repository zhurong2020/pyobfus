"""Token-based detection of f-string syntax introduced by PEP 701.

feature_version on ast.parse does not enforce the old f-string lexer on
Python 3.12. Inspect tokens instead; never execute the inspected source.
"""

import ast
import io
import re
import token
import tokenize
from dataclasses import dataclass, field
from typing import List, Tuple

from pyobfus.exceptions import FStringCompatibilityError


@dataclass
class _Field:
    brackets: List[str] = field(default_factory=list)
    format_spec: bool = False


@dataclass
class _Frame:
    quote: str
    previous: Tuple[int, int]
    fields: List[_Field] = field(default_factory=list)


def pep701_locations(source: str) -> List[Tuple[int, int]]:
    """Return locations requiring the PEP 701 lexer.

    Pre-3.12 tokenizers cannot parse valid PEP 701 sources and have no
    FSTRING_START tokens. Literal text (including format-spec text) is not
    an expression, but a nested f-string belongs to its enclosing expression.
    """
    start = getattr(token, "FSTRING_START", None)
    end = getattr(token, "FSTRING_END", None)
    if start is None:
        return []
    frames: List[_Frame] = []
    lines = source.splitlines(keepends=True)
    locations = set()

    def between(a: Tuple[int, int], b: Tuple[int, int]) -> str:
        if a[0] == b[0]:
            return lines[a[0] - 1][a[1] : b[1]]
        return lines[a[0] - 1][a[1] :] + "".join(lines[a[0] : b[0] - 1]) + lines[b[0] - 1][: b[1]]

    for item in tokenize.generate_tokens(io.StringIO(source).readline):
        for frame in frames:
            if frame.fields:
                text = between(frame.previous, item.start) + item.string
                expression = any(not f.format_spec for f in frame.fields)
                if (
                    (expression and ("\\" in text or item.type == tokenize.COMMENT))
                    or (len(frame.quote) == 1 and "\n" in text)
                    or (item.type in (tokenize.STRING, start) and frame.quote in item.string)
                ):
                    locations.add(item.start)
            frame.previous = item.end
        if item.type == start:
            match = re.search(r"('''|\"\"\"|'|\")$", item.string)
            if match:
                frames.append(_Frame(match.group(), item.end))
        elif item.type == end:
            frames.pop()
        elif frames and item.type == tokenize.OP:
            fields = frames[-1].fields
            if item.string == "{" and (not fields or fields[-1].format_spec):
                fields.append(_Field())
                if len(fields) > 2:
                    # The old lexer allowed only one nested format-spec field.
                    locations.add(item.start)
            elif fields:
                current = fields[-1]
                if item.string in ("(", "[", "{"):
                    current.brackets.append(item.string)
                elif item.string == "}" and not current.brackets:
                    fields.pop()
                elif item.string in (")", "]", "}") and current.brackets:
                    current.brackets.pop()
                elif item.string == ":" and not current.brackets:
                    current.format_spec = True
    return sorted(locations)


def pep646_locations(source: str) -> List[Tuple[int, int]]:
    """Find bare starred tuple subscripts using AST locations and tokens.

    AST identifies subscripts without mistaking lists, strings or comments for
    them. Tokens distinguish enclosing parentheses, which AST discards.
    On pre-3.11 builders bare starred subscripts already fail parsing; callers
    reject that invalid generated syntax too.
    """
    locations = []
    for node in ast.walk(ast.parse(source)):
        if not (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Tuple)
            and any(isinstance(elt, ast.Starred) for elt in node.slice.elts)
        ):
            continue
        segment = ast.get_source_segment(source, node.slice)
        assert segment is not None
        tokens = [
            item.string
            for item in tokenize.generate_tokens(io.StringIO(segment).readline)
            if item.type
            not in (tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT)
        ]
        enclosed = False
        if tokens and tokens[0] == "(":
            depth = 0
            for index, value in enumerate(tokens):
                if value == "(":
                    depth += 1
                elif value == ")":
                    depth -= 1
                    if depth == 0:
                        enclosed = index == len(tokens) - 1
                        break
        if not enclosed:
            locations.append((node.slice.lineno, node.slice.col_offset))
    return sorted(locations)


def ensure_fstring_compatibility(original: str, generated: str, filename: str) -> None:
    """Reject newly introduced PEP 701/646 syntax before writing output.

    Keep the existing exception and JSON error_type for compatibility.
    """
    if not pep701_locations(original):
        locations = pep701_locations(generated)
        if locations:
            line, column = locations[0]
            raise FStringCompatibilityError(
                f"{filename}:{line}:{column + 1}: generated f-string requires Python >= 3.12 "
                "although the source does not use PEP 701 syntax"
            )
    try:
        original_locations = pep646_locations(original)
        locations = pep646_locations(generated)
    except SyntaxError as exc:
        raise FStringCompatibilityError(
            f"{filename}:{exc.lineno}:{exc.offset}: generated syntax is invalid on this "
            "builder (bare starred subscripts require Python >= 3.11): " + exc.msg
        ) from exc
    if not original_locations and locations:
        line, column = locations[0]
        raise FStringCompatibilityError(
            f"{filename}:{line}:{column + 1}: generated subscript requires Python >= 3.11 "
            "although the source does not use PEP 646 starred subscript syntax"
        )

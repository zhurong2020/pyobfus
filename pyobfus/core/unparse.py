"""Shared source generation with starred subscript compatibility.

CPython 3.13 f-string quote selection is backported only for 3.12.0–3.12.8.

Adapted from CPython Lib/ast.py (PSF license). Keep the backport local:
other builders retain native formatting except for starred subscript tuples.
"""

import ast
import sys
from typing import cast

_ALL_QUOTES = ("'", '"', "'" * 3, '"' * 3)
_MULTI_QUOTES = ("'" * 3, '"' * 3)
if sys.version_info >= (3, 14):
    from _ast_unparse import Unparser as _NativeUnparser
else:
    _NativeUnparser = getattr(ast, "_Unparser")
_BaseUnparser = getattr(ast, "_Unparser", object)


class SubscriptUnparser(_NativeUnparser):  # type: ignore[misc, valid-type]
    """Keep starred tuple subscripts valid on Python 3.9 and 3.10."""

    def visit_Subscript(self, node):
        if (
            isinstance(node.slice, ast.Tuple)
            and any(isinstance(elt, ast.Starred) for elt in node.slice.elts)
            and not any(isinstance(elt, ast.Slice) for elt in node.slice.elts)
        ):
            # The native method bypasses visit_Tuple and omits its parentheses.
            # Use its own precedence enum (moved to _ast_unparse in 3.14).
            precedence = _NativeUnparser.visit_Subscript.__globals__["_Precedence"]
            self.set_precedence(precedence.ATOM, node.value)
            self.traverse(node.value)
            with self.delimit("[", "]"):
                with self.delimit("(", ")"):
                    self.items_view(self.traverse, node.slice.elts)
        else:
            # Mixed slices such as a[1:2, *xs] already require 3.11+ and
            # cannot be parenthesized: (1:2, *xs) is not a valid tuple.
            super().visit_Subscript(node)


class FStringUnparser(SubscriptUnparser):  # type: ignore[misc, valid-type]
    """Backport the quote selector and its mutually dependent methods."""

    def visit(self, node):
        # Direct users receive the same safe fallback as the versioned wrapper.
        # CPython 3.14 moved precedence helpers out of the ast module.
        if not _backport_available():
            return ast.unparse(node)
        return super().visit(node)

    def _str_literal_helper(
        self, string, *, quote_types=_ALL_QUOTES, escape_special_whitespace=False
    ):
        """Helper for writing string literals, minimizing escapes.
        Returns the tuple (string literal to write, possible quote types).
        """

        def escape_char(c):
            # \n and \t are non-printable, but we only escape them if
            # escape_special_whitespace is True
            if not escape_special_whitespace and c in "\n\t":
                return c
            # Always escape backslashes and other non-printable characters
            if c == "\\" or not c.isprintable():
                return c.encode("unicode_escape").decode("ascii")
            return c

        escaped_string = "".join(map(escape_char, string))
        possible_quotes = quote_types
        if "\n" in escaped_string:
            possible_quotes = [q for q in possible_quotes if q in _MULTI_QUOTES]
        possible_quotes = [q for q in possible_quotes if q not in escaped_string]
        if not possible_quotes:
            # If there aren't any possible_quotes, fallback to using repr
            # on the original string. Try to use a quote from quote_types,
            # e.g., so that we use triple quotes for docstrings.
            string = repr(string)
            quote = next((q for q in quote_types if string[0] in q), string[0])
            return string[1:-1], [quote]
        if escaped_string:
            # Sort so that we prefer '''"''' over """\""""
            possible_quotes.sort(key=lambda q: q[0] == escaped_string[-1])
            # If we're using triple quotes and we'd need to escape a final
            # quote, escape it
            if possible_quotes[0][0] == escaped_string[-1]:
                assert len(possible_quotes[0]) == 3
                escaped_string = escaped_string[:-1] + "\\" + escaped_string[-1]
        return escaped_string, possible_quotes

    def _write_str_avoiding_backslashes(self, string, *, quote_types=_ALL_QUOTES):
        """Write string literal value with a best effort attempt to avoid backslashes."""
        string, quote_types = self._str_literal_helper(string, quote_types=quote_types)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{string}{quote_type}")

    def visit_JoinedStr(self, node):
        self.write("f")

        fstring_parts = []
        for value in node.values:
            with self.buffered() as buffer:
                self._write_fstring_inner(value)
            fstring_parts.append(("".join(buffer), isinstance(value, ast.Constant)))

        new_fstring_parts = []
        quote_types = list(_ALL_QUOTES)
        fallback_to_repr = False
        for value, is_constant in fstring_parts:
            if is_constant:
                value, new_quote_types = self._str_literal_helper(
                    value,
                    quote_types=quote_types,
                    escape_special_whitespace=True,
                )
                if set(new_quote_types).isdisjoint(quote_types):
                    fallback_to_repr = True
                    break
                quote_types = new_quote_types
            else:
                if "\n" in value:
                    quote_types = [q for q in quote_types if q in _MULTI_QUOTES]
                    assert quote_types

                new_quote_types = [q for q in quote_types if q not in value]
                if new_quote_types:
                    quote_types = new_quote_types
            new_fstring_parts.append(value)

        if fallback_to_repr:
            # If we weren't able to find a quote type that works for all parts
            # of the ast.JoinedStr, fallback to using repr and triple single quotes.
            quote_types = ["'''"]
            new_fstring_parts.clear()
            for value, is_constant in fstring_parts:
                if is_constant:
                    value = repr('"' + value)  # force repr to use single quotes
                    expected_prefix = "'\""
                    assert value.startswith(expected_prefix), repr(value)
                    value = value[len(expected_prefix) : -1]
                new_fstring_parts.append(value)

        value = "".join(new_fstring_parts)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{value}{quote_type}")

    def _write_fstring_inner(self, node, is_format_spec=False):
        if isinstance(node, ast.JoinedStr):
            # for both the f-string itself, and format_spec
            for value in node.values:
                self._write_fstring_inner(value, is_format_spec=is_format_spec)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.replace("{", "{{").replace("}", "}}")

            if is_format_spec:
                value = value.replace("\\", "\\\\")
                value = value.replace("'", "\\'")
                value = value.replace('"', '\\"')
                value = value.replace("\n", "\\n")
            self.write(value)
        elif isinstance(node, ast.FormattedValue):
            self.visit_FormattedValue(node)
        else:
            raise ValueError(f"Unexpected node inside ast.JoinedStr, {node!r}")

    def visit_FormattedValue(self, node):
        def unparse_inner(inner):
            unparser = type(self)()
            unparser.set_precedence(ast._Precedence.TEST.next(), inner)
            return unparser.visit(inner)

        with self.delimit("{", "}"):
            expr = unparse_inner(node.value)
            if expr.startswith("{"):
                # Separate pair of opening brackets as "{ {"
                self.write(" ")
            self.write(expr)
            if node.conversion != -1:
                self.write(f"!{chr(node.conversion)}")
            if node.format_spec:
                self.write(":")
                self._write_fstring_inner(node.format_spec, is_format_spec=True)


def _backport_available():
    precedence = getattr(ast, "_Precedence", None)
    test = getattr(precedence, "TEST", None)
    return all(
        callable(getattr(_BaseUnparser, name, None))
        for name in ("buffered", "write", "delimit", "set_precedence", "visit")
    ) and callable(getattr(test, "next", None))


def unparse(tree: ast.AST) -> str:
    """Preserve starred tuple parentheses on every supported builder.

    Keep the f-string backport restricted to affected CPython patch releases.
    The source/output compatibility guard also rejects syntax regressions.
    """
    if (3, 12) <= sys.version_info < (3, 12, 9) and _backport_available():
        return cast(str, FStringUnparser().visit(tree))
    if any(
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Tuple)
        and any(isinstance(elt, ast.Starred) for elt in node.slice.elts)
        for node in ast.walk(tree)
    ):
        return cast(str, SubscriptUnparser().visit(tree))
    return ast.unparse(tree)

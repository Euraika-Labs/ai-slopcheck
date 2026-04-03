"""Lightweight string/comment context detector.

Determines if a regex match position falls inside a string literal,
comment, or regex literal — without requiring tree-sitter or any
external dependency. Uses a single-pass character scanner.
"""
from __future__ import annotations

_JS_REGEX_PREV = frozenset("=([,!&|:?{;+-*/%^~<>")


def is_in_non_code_context(
    line: str, match_start: int, lang: str = "generic"
) -> bool:
    """Return True if match_start is inside a string, comment, or regex.

    lang: "py" | "js" | "go" | "generic"
    Does NOT track multi-line state (triple-quotes, /* */) across lines.
    Callers must handle cross-line block comments separately.
    """
    state = "code"
    quote_char = ""
    i = 0
    n = len(line)

    while i < match_start:
        ch = line[i]
        nxt = line[i + 1] if i + 1 < n else ""

        if state == "code":
            if ch == "#" and lang in ("py", "generic"):
                return True  # rest of line is comment
            if ch == "/" and nxt == "/" and lang in ("js", "go", "generic"):
                return True  # rest of line is comment
            if ch == "/" and nxt == "*":
                state = "block_comment"
                i += 2
                continue
            if ch in ('"', "'"):
                state = "string"
                quote_char = ch
                i += 1
                continue
            if ch == "`" and lang in ("js", "generic"):
                state = "template"
                i += 1
                continue
            if ch == "/" and lang in ("js", "generic"):
                prev = line[:i].rstrip()
                if not prev or prev[-1] in _JS_REGEX_PREV:
                    state = "regex"
                    i += 1
                    continue
        elif state == "string":
            if ch == "\\":
                i += 2
                continue
            if ch == quote_char:
                state = "code"
                quote_char = ""
        elif state == "template":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                state = "code"
        elif state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "/":
                state = "code"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 2
                continue

        i += 1

    return state != "code"

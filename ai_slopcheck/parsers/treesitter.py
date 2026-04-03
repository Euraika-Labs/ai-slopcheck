"""Tree-sitter adapter for context-aware scanning.

Provides utilities to determine if a source position falls inside a string,
comment, or other non-code context. Gracefully falls back to None when
tree-sitter grammars are not installed.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256

try:
    from tree_sitter import Language, Node, Parser

    _TS_AVAILABLE = True
except ImportError:
    _TS_AVAILABLE = False

# Extension → (grammar module name, language factory)
_LANG_MAP: dict[str, str] = {
    ".py": "tree_sitter_python",
    ".js": "tree_sitter_javascript",
    ".jsx": "tree_sitter_javascript",
    ".ts": "tree_sitter_typescript",
    ".tsx": "tree_sitter_typescript",
    ".go": "tree_sitter_go",
}

# Node types that represent non-code context across languages
_STRING_NODE_TYPES = frozenset({
    # Python
    "string", "string_content", "concatenated_string",
    # JS/TS
    "string_fragment", "template_string",
    "template_substitution",
    # Go
    "raw_string_literal", "interpreted_string_literal",
})

_COMMENT_NODE_TYPES = frozenset({
    "comment", "line_comment", "block_comment",
})

_NON_CODE_NODE_TYPES = _STRING_NODE_TYPES | _COMMENT_NODE_TYPES


@lru_cache(maxsize=8)
def _get_parser(ext: str) -> Parser | None:
    """Get a cached parser for the given file extension."""
    if not _TS_AVAILABLE:
        return None

    module_name = _LANG_MAP.get(ext)
    if module_name is None:
        return None

    try:
        mod = __import__(module_name)
        # Handle tree_sitter_typescript which has .tsx() and .typescript()
        if module_name == "tree_sitter_typescript":
            if ext == ".tsx":
                lang_fn = getattr(mod, "language_tsx", mod.language)
            else:
                lang_fn = getattr(
                    mod, "language_typescript", mod.language
                )
            lang = Language(lang_fn())
        else:
            lang = Language(mod.language())
        parser = Parser(lang)
        return parser
    except Exception:
        return None


# File content → parsed tree cache (avoids re-parsing same file per rule)
_tree_cache: dict[str, Node] = {}


def parse_file(content: str, ext: str) -> Node | None:
    """Parse file content and return the root node. Cached by content hash."""
    cache_key = sha256(
        (content + ext).encode("utf-8")
    ).hexdigest()[:16]

    if cache_key in _tree_cache:
        return _tree_cache[cache_key]

    parser = _get_parser(ext)
    if parser is None:
        return None

    try:
        tree = parser.parse(content.encode("utf-8"))
        root = tree.root_node
        # Keep cache bounded
        if len(_tree_cache) > 50:
            _tree_cache.clear()
        _tree_cache[cache_key] = root
        return root
    except Exception:
        return None


def _node_at_position(
    root: Node, line: int, column: int
) -> Node | None:
    """Find the deepest node at the given 0-indexed line and column."""
    node = root.descendant_for_point_range(
        (line, column), (line, column)
    )
    return node


def is_in_string(
    content: str, ext: str, line_1indexed: int, column: int = 0
) -> bool | None:
    """Check if a position is inside a string literal.

    Returns True/False if tree-sitter is available, None otherwise.
    """
    root = parse_file(content, ext)
    if root is None:
        return None

    node = _node_at_position(root, line_1indexed - 1, column)
    if node is None:
        return None

    # Walk up to check if any ancestor is a string node
    current = node
    while current is not None:
        if current.type in _STRING_NODE_TYPES:
            return True
        current = current.parent
    return False


def is_in_comment(
    content: str, ext: str, line_1indexed: int, column: int = 0
) -> bool | None:
    """Check if a position is inside a comment.

    Returns True/False if tree-sitter is available, None otherwise.
    """
    root = parse_file(content, ext)
    if root is None:
        return None

    node = _node_at_position(root, line_1indexed - 1, column)
    if node is None:
        return None

    current = node
    while current is not None:
        if current.type in _COMMENT_NODE_TYPES:
            return True
        current = current.parent
    return False


def is_in_non_code(
    content: str, ext: str, line_1indexed: int, column: int = 0
) -> bool | None:
    """Check if a position is inside a string OR comment.

    Returns True/False if tree-sitter is available, None otherwise.
    """
    root = parse_file(content, ext)
    if root is None:
        return None

    node = _node_at_position(root, line_1indexed - 1, column)
    if node is None:
        return None

    current = node
    while current is not None:
        if current.type in _NON_CODE_NODE_TYPES:
            return True
        current = current.parent
    return False


def is_available() -> bool:
    """Return True if tree-sitter and at least one grammar are installed."""
    return _TS_AVAILABLE

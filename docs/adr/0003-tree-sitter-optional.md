# ADR 0003: Tree-sitter as an optional dependency with graceful fallback

## Status

Accepted

## Context

Several rules need to determine whether a regex match falls inside a string literal or a comment, not in executable code. Without this check, rules generate false positives on documentation strings, test fixtures, and inline examples.

Two approaches were considered:

**A. Make tree-sitter a hard dependency.**
Accurate and uniform. All rules behave consistently. Requires every user to install grammars for every language they scan.

**B. Make tree-sitter optional with fallback.**
Lower install friction. Operators who do not care about reduced-precision fallback can skip the grammar packages. Rules degrade gracefully rather than crashing.

A third tool, `context_filter.py`, was also built: a single-pass character scanner that detects string/comment context without any external dependency. It covers the common case well enough for most rules.

## Decision

Tree-sitter is an **optional dependency**. Installing it improves precision; omitting it does not break the scanner.

Rules that want AST-level context detection call `treesitter.is_in_non_code(content, ext, line, col)`. This returns:

- `True` / `False` if tree-sitter and the relevant grammar are installed
- `None` if not available

When `None` is returned, the rule falls back to `context_filter.is_in_non_code_context(line, match_start, lang)` or skips the context check entirely based on its own false-positive tolerance.

Grammar support is limited to languages where rules concretely benefit: Python, JavaScript/JSX, TypeScript/TSX, Go.

## Implementation details

**Parser cache:** `_get_parser(ext)` is `@lru_cache(maxsize=8)`. Parsers are expensive to construct; they are reused across all files with the same extension.

**Parse cache:** `parse_file(content, ext)` caches parsed trees in a module-level dict keyed by `sha256(content + ext)[:16]`. This means the same file is parsed at most once per scan, even when multiple rules check the same content. The cache is capped at 50 entries and cleared entirely on overflow to avoid unbounded growth.

**Thread safety:** The tree cache is a plain dict. In CPython, dict reads/writes are GIL-protected for individual operations. The bounded-clear strategy means concurrent eviction under high load is safe but may redundantly clear recently-added entries; this is acceptable.

**Import isolation:** The `try/except ImportError` at the top of `treesitter.py` sets `_TS_AVAILABLE = False`. All public functions check this flag before attempting to use tree-sitter APIs. No rule module imports tree-sitter directly.

## Consequences

### Positive

- Zero-friction install for users who only need baseline precision
- Rules do not crash in environments without grammar packages
- Adding a new grammar requires one line in `_LANG_MAP` and an optional install
- Parse caching eliminates redundant work when multiple rules scan the same file

### Negative

- Two code paths per rule that uses context detection (with and without tree-sitter)
- Rules must be tested in both modes
- The module-level parse cache is not explicitly invalidated between `scan_paths` calls in long-lived processes (acceptable for CLI usage; not a concern for the current product shape)

## Follow-up

If future rules require tree-sitter for correctness rather than just precision improvement, promote the relevant grammars to recommended (not required) in the install docs.

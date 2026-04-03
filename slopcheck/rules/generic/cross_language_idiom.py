from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.engine.context_filter import is_in_non_code_context
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.parsers.treesitter import is_in_non_code as ts_is_in_non_code
from slopcheck.rules.base import Rule

# ---------------------------------------------------------------------------
# Pattern sets per language (extension group → list of (regex, description))
# ---------------------------------------------------------------------------

# Python files: JS/Go idioms that don't belong
_PY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bself\b.*\.push\s*\("),
     "`.push()` is JS — use `.append()` in Python"),
    (re.compile(r"(?<!['\"])(?<!\w)null(?!\w)(?!['\"])"),
     "`null` is JS/Java — use `None` in Python"),
    (re.compile(r"\bconsole\.log\s*\("),
     "`console.log(` is JS — use `print()` in Python"),
]

# JS/TS/JSX/TSX files: Python/Go idioms that don't belong
_JS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!['\"])(?<!\w)nil(?!\w)(?!['\"])"),
     "`nil` is Go — use `null`/`undefined` in JS/TS"),
    (re.compile(r"^\s*def\s+\w+\s*\("),
     "`def` is Python — use `function`/arrow in JS/TS"),
    (re.compile(r"\belif\b"),
     "`elif` is Python — use `else if` in JS/TS"),
    (re.compile(r"\w\s*:=\s*\w"),
     "`:=` is Go — use `const`/`let` in JS/TS"),
]

# Go files: Python/JS idioms that don't belong
_GO_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!['\"])(?<!\w)None(?!\w)(?!['\"])"),
     "`None` is Python — use `nil` in Go"),
    (re.compile(r"\bself\."),
     "`self.` is Python — use receiver in Go"),
    (re.compile(r"\bthis\."),
     "`this.` is JS/TS — use receiver in Go"),
    (re.compile(r"\bconsole\.log\s*\("),
     "`console.log(` is JS — use `fmt.Println` in Go"),
]

_JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}


def _pick_patterns(relative_path: str) -> list[tuple[re.Pattern[str], str]] | None:
    ext = Path(relative_path).suffix.lower()
    if ext == ".py":
        return _PY_PATTERNS
    if ext in _JS_EXTENSIONS:
        return _JS_PATTERNS
    if ext == ".go":
        return _GO_PATTERNS
    return None


def _looks_like_string_literal(line: str, start: int) -> bool:
    """Very rough heuristic: if the match position is inside a quoted region, skip it."""
    # Count unescaped single and double quotes before the match start.
    before = line[:start]
    # Collapse escape sequences crudely.
    before = before.replace("\\'", "").replace('\\"', "")
    single_count = before.count("'")
    double_count = before.count('"')
    return (single_count % 2 == 1) or (double_count % 2 == 1)


class CrossLanguageIdiomRule(Rule):
    rule_id = "cross_language_idiom"
    title = "Cross-language idiom — wrong language construct for this file type"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.cross_language_idiom
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        patterns = _pick_patterns(relative_path)
        if patterns is None:
            return []

        ext = Path(relative_path).suffix.lower()
        lang = "py" if ext == ".py" else "go" if ext == ".go" else "js"

        findings: list[Finding] = []
        in_multiline_string = False
        for lineno, line in enumerate(content.splitlines(), start=1):
            # Track multi-line string state (triple quotes)
            triple_count = line.count('"""') + line.count("'''")
            if triple_count % 2 == 1:
                in_multiline_string = not in_multiline_string
            if in_multiline_string:
                continue

            # Skip comment-only lines
            stripped = line.lstrip()
            if stripped.startswith(("#", "//", "*")):
                continue

            # Skip lines inside regex literals (JS)
            if "/.*" in line or "RegExp" in line:
                continue

            for pattern, description in patterns:
                m = pattern.search(line)
                if not m:
                    continue
                # Tree-sitter check (more accurate) with fallback
                ext = Path(relative_path).suffix.lower()
                ts_result = ts_is_in_non_code(
                    content, ext, lineno, m.start()
                )
                if ts_result is True:
                    continue
                # Fallback: char-scanner if tree-sitter unavailable
                if ts_result is None and is_in_non_code_context(
                    line, m.start(), lang=lang
                ):
                    continue
                evidence = m.group(0).strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Cross-language idiom detected: {description}. "
                            "This construct belongs to a different language and will not "
                            "work as intended in this file."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion=description,
                        tags=["cross-language", "wrong-idiom"],
                    )
                )
                break  # One finding per line is enough.
        return findings

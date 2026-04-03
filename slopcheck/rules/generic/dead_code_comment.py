from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Comment prefixes by file extension
COMMENT_PREFIXES: dict[str, str] = {
    ".py": "#",
    ".js": "//", ".jsx": "//", ".ts": "//", ".tsx": "//",
    ".go": "//",
    ".rs": "//",
    ".java": "//", ".kt": "//",
    ".cs": "//",
    ".c": "//", ".cc": "//", ".cpp": "//", ".h": "//", ".hpp": "//",
}

# Patterns that indicate commented-out code (not prose comments)
CODE_IN_COMMENT_RE = re.compile(
    r"(?:"
    r"(?:(?:const|let|var|final)\s+)?"
    r"[\w.\[\]\"']+\s*(?:=(?!=)|!=|==|\+=|-=|\*=|/=)\s*\S"  # assignment
    r"|(?:if|for|while)\s+.*[:{]\s*$"  # control flow with colon/brace
    r"|(?:return|yield|raise|del|assert)\s+\S"  # statements with arg
    r"|\w+\s*\([^)]*\)\s*;?\s*$"  # function call (optional semicolon)
    r"|(?:import|from|require)\s+\w+"  # import
    r"|(?:class|def|function)\s+\w+\s*[\(:{]"  # definitions
    r"|(?:self|this|cls)\.\w+\s*[=(]"  # member access
    r")"
)


# English stopwords — if 2+ appear in a comment line, it's prose not code
_STOPWORDS = frozenset({
    "the", "and", "this", "that", "for", "with", "from",
    "are", "was", "were", "been", "being", "have", "has",
    "will", "would", "could", "should", "may", "might",
    "also", "into", "when", "where", "which", "while",
    "about", "between", "through", "during", "before",
    "after", "above", "below", "each", "every", "both",
    "then", "than", "because", "since", "until", "unless",
})


def _is_prose(text: str) -> bool:
    """Return True if text looks like English prose, not code."""
    words = set(text.lower().split())
    return len(words & _STOPWORDS) >= 2


class DeadCodeCommentRule(Rule):
    rule_id = "dead_code_comment"
    title = "Commented-out code block"
    supported_extensions = set(COMMENT_PREFIXES.keys())

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.dead_code_comment
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        # Skip paths matching exclusion patterns
        from fnmatch import fnmatch

        if any(fnmatch(relative_path, p) for p in rule_config.excluded_paths):
            return []

        ext = Path(relative_path).suffix.lower()
        prefix = COMMENT_PREFIXES.get(ext)
        if prefix is None:
            return []

        min_lines = rule_config.min_consecutive_lines
        lines = content.splitlines()
        findings: list[Finding] = []

        run_start: int | None = None
        run_length = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if this is a comment line with code content
            is_code_comment = False
            if stripped.startswith(prefix):
                comment_body = stripped[len(prefix):].strip()
                if (
                    comment_body
                    and CODE_IN_COMMENT_RE.search(comment_body)
                    and not _is_prose(comment_body)
                ):
                    is_code_comment = True

            if is_code_comment:
                if run_start is None:
                    run_start = i
                run_length += 1
            else:
                if run_start is not None and run_length >= min_lines:
                    findings.append(
                        self._make_finding(
                            relative_path, run_start + 1, run_length
                        )
                    )
                run_start = None
                run_length = 0

        # Handle run at end of file
        if run_start is not None and run_length >= min_lines:
            findings.append(
                self._make_finding(relative_path, run_start + 1, run_length)
            )

        return findings

    def _make_finding(
        self, relative_path: str, start_line: int, count: int
    ) -> Finding:
        return self.build_finding(
            relative_path=relative_path,
            line=start_line,
            message=(
                f"Block of {count} consecutive commented-out code lines. "
                "This may be leftover from AI-assisted code generation."
            ),
            severity=Severity.NOTE,
            confidence=Confidence.MEDIUM,
            evidence=f"commented_code_block:{count}_lines",
            suggestion="Delete the commented-out code or uncomment it if still needed.",
            tags=["dead-code", "ai-artifact"],
        )

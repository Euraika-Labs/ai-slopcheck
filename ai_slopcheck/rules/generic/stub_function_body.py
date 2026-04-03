from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Matches a Python function/method definition
FUNC_DEF_RE = re.compile(r"^(\s*)def\s+(\w+)\s*\(")

# Matches a stub return statement (bare literal only)
STUB_RETURN_RE = re.compile(
    r"^\s*return\s+(?:None|True|False|\[\]|\{\}|\(\)|\"\"|\'\'"
    r"|0|0\.0|-1)\s*$"
)

# Matches pass or ellipsis (standalone stub body)
STUB_PASS_RE = re.compile(r"^\s*(?:pass|\.\.\.)\s*$")

# Matches a docstring opener
DOCSTRING_RE = re.compile(r'^\s*(?:"""|\'\'\'|"|\')')

# Decorators that mark intentional stubs
ABSTRACT_RE = re.compile(r"^\s*@(?:abstractmethod|overload)")

# Function name prefixes that elevate confidence
HIGH_CONFIDENCE_PREFIXES = ("get_", "fetch_", "load_", "compute_", "calculate_", "process_")


class StubFunctionBodyRule(Rule):
    rule_id = "stub_function_body"
    title = "Stub function body"
    supported_extensions = {".py"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.stub_function_body
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        excluded = set(rule_config.excluded_function_patterns)
        lines = content.splitlines()
        findings: list[Finding] = []
        i = 0

        while i < len(lines):
            # Check for @abstractmethod decorator
            if ABSTRACT_RE.match(lines[i]):
                i += 1
                # Skip the decorated function entirely
                while i < len(lines) and not FUNC_DEF_RE.match(lines[i]):
                    i += 1
                if i < len(lines):
                    i = self._skip_function(lines, i)
                continue

            func_match = FUNC_DEF_RE.match(lines[i])
            if func_match is None:
                i += 1
                continue

            func_indent = len(func_match.group(1))
            func_name = func_match.group(2)
            func_line = i + 1  # 1-indexed

            if func_name in excluded:
                i = self._skip_function(lines, i)
                continue

            # Scan the function body
            body_start = i + 1
            # Handle multi-line def (continuation lines)
            while body_start < len(lines) and not lines[body_start - 1].rstrip().endswith(":"):
                body_start += 1
            if body_start >= len(lines):
                i += 1
                continue

            # Collect non-blank, non-comment, non-docstring body lines
            body_lines: list[str] = []
            j = body_start
            in_docstring = False
            docstring_char = ""

            while j < len(lines):
                line = lines[j]
                stripped = line.strip()

                # Check indentation — if we've dedented back to func level, body is over
                if stripped and not in_docstring:
                    line_indent = len(line) - len(line.lstrip())
                    if line_indent <= func_indent:
                        break

                # Handle docstrings
                if in_docstring:
                    if docstring_char in stripped:
                        in_docstring = False
                    j += 1
                    continue

                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    if stripped.count(docstring_char) >= 2:
                        # Single-line docstring
                        j += 1
                        continue
                    in_docstring = True
                    j += 1
                    continue

                # Skip blank lines and comments
                if not stripped or stripped.startswith("#"):
                    j += 1
                    continue

                body_lines.append(stripped)
                j += 1

            # Check if the body is a single stub statement
            if len(body_lines) == 1:
                stmt = body_lines[0]
                if STUB_RETURN_RE.match(stmt) or STUB_PASS_RE.match(stmt):
                    confidence = Confidence.HIGH if func_name.startswith(
                        HIGH_CONFIDENCE_PREFIXES
                    ) else Confidence.MEDIUM
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=func_line,
                            message=(
                                f"Function `{func_name}` has a stub body (`{stmt.strip()}`). "
                                "This may be an incomplete AI-generated implementation."
                            ),
                            severity=Severity.WARNING,
                            confidence=confidence,
                            evidence=f"{func_name}:{stmt.strip()}",
                            suggestion=(
                                "Implement the function body or mark it "
                                "as intentionally empty."
                            ),
                            tags=["ai-stub", "incomplete"],
                        )
                    )

            i = max(j, i + 1)

        return findings

    @staticmethod
    def _skip_function(lines: list[str], func_line_idx: int) -> int:
        """Skip past a function body by tracking indentation."""
        func_match = FUNC_DEF_RE.match(lines[func_line_idx])
        if func_match is None:
            return func_line_idx + 1
        func_indent = len(func_match.group(1))
        j = func_line_idx + 1
        while j < len(lines):
            stripped = lines[j].strip()
            if stripped:
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                if line_indent <= func_indent:
                    return j
            j += 1
        return j

from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

_PYTHON_EXTS = {".py"}
_BRACE_EXTS = {".js", ".jsx", ".ts", ".tsx", ".go"}
_OPEN_BRACE_RE = re.compile(r"\{")
_CLOSE_BRACE_RE = re.compile(r"\}")


class DeepNestingRule(Rule):
    rule_id = "deep_nesting"
    title = "Deeply nested code block"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.deep_nesting
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        max_depth = rule_config.max_depth

        if ext in _PYTHON_EXTS:
            return self._scan_python(relative_path, content, max_depth)
        elif ext in _BRACE_EXTS:
            return self._scan_brace(relative_path, content, max_depth)
        return []

    def _scan_python(
        self, relative_path: str, content: str, max_depth: int
    ) -> list[Finding]:
        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            leading = len(line) - len(stripped)
            # Each indent level is 4 spaces in Python convention
            depth = leading // 4
            if depth > max_depth:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Code nested {depth} levels deep (max {max_depth}). "
                            "Deep nesting makes code hard to read and test."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=line.strip(),
                        suggestion=(
                            "Extract deeply nested logic into helper functions, "
                            "or use early returns to reduce nesting."
                        ),
                        tags=["complexity", "readability"],
                    )
                )
        return findings

    def _scan_brace(
        self, relative_path: str, content: str, max_depth: int
    ) -> list[Finding]:
        findings: list[Finding] = []
        depth = 0
        reported_lines: set[int] = set()
        for lineno, line in enumerate(content.splitlines(), start=1):
            opens = len(_OPEN_BRACE_RE.findall(line))
            closes = len(_CLOSE_BRACE_RE.findall(line))
            depth += opens
            if depth > max_depth and lineno not in reported_lines:
                reported_lines.add(lineno)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Code nested {depth} brace levels deep (max {max_depth}). "
                            "Deep nesting makes code hard to read and test."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=line.strip(),
                        suggestion=(
                            "Extract deeply nested logic into helper functions, "
                            "or use early returns to reduce nesting."
                        ),
                        tags=["complexity", "readability"],
                    )
                )
            depth -= closes
            if depth < 0:
                depth = 0
        return findings

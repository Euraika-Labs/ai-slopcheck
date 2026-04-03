from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

_PY_DEF_RE = re.compile(r"^(\s*)def\s+\w+")
_JS_FUNC_RE = re.compile(
    r"\b(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\()"
)
_JS_ARROW_BRACE_RE = re.compile(r"=>\s*\{")
_GO_FUNC_RE = re.compile(r"^func\s+")


class LargeFunctionRule(Rule):
    rule_id = "large_function"
    title = "Function exceeds maximum line count"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.large_function
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        max_lines = rule_config.max_lines
        lines = content.splitlines()

        if ext == ".py":
            return self._scan_python(relative_path, lines, max_lines)
        elif ext in {".js", ".jsx", ".ts", ".tsx"}:
            return self._scan_js(relative_path, lines, max_lines)
        elif ext == ".go":
            return self._scan_go(relative_path, lines, max_lines)
        return []

    def _scan_python(
        self, relative_path: str, lines: list[str], max_lines: int
    ) -> list[Finding]:
        findings: list[Finding] = []
        func_starts: list[tuple[int, int, str]] = []  # (lineno, indent, name)

        for lineno, line in enumerate(lines, start=1):
            m = _PY_DEF_RE.match(line)
            if m:
                indent = len(m.group(1))
                func_starts.append((lineno, indent, line.strip()))

        for i, (start_line, indent, header) in enumerate(func_starts):
            # Find end: next def at same or lower indent, or EOF
            end_line = len(lines)
            for j in range(i + 1, len(func_starts)):
                next_start, next_indent, _ = func_starts[j]
                if next_indent <= indent:
                    end_line = next_start - 1
                    break

            func_len = end_line - start_line + 1
            if func_len > max_lines:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=start_line,
                        message=(
                            f"Function is {func_len} lines long (max {max_lines}). "
                            "Large functions are harder to test, review, and maintain."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.LOW,
                        evidence=header,
                        suggestion=(
                            "Break this function into smaller, focused helper functions "
                            "with single responsibilities."
                        ),
                        tags=["complexity", "maintainability"],
                    )
                )

        return findings

    def _scan_js(
        self, relative_path: str, lines: list[str], max_lines: int
    ) -> list[Finding]:
        findings: list[Finding] = []
        func_starts: list[tuple[int, str]] = []

        for lineno, line in enumerate(lines, start=1):
            if _JS_FUNC_RE.search(line) or _JS_ARROW_BRACE_RE.search(line):
                func_starts.append((lineno, line.strip()))

        for start_line, header in func_starts:
            # Walk forward counting brace depth to find end of function
            depth = 0
            end_line = start_line
            started = False
            for i, line in enumerate(lines[start_line - 1 :], start=start_line):
                depth += line.count("{") - line.count("}")
                if depth > 0:
                    started = True
                if started and depth <= 0:
                    end_line = i
                    break

            func_len = end_line - start_line + 1
            if func_len > max_lines:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=start_line,
                        message=(
                            f"Function is {func_len} lines long (max {max_lines}). "
                            "Large functions are harder to test, review, and maintain."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.LOW,
                        evidence=header,
                        suggestion=(
                            "Break this function into smaller, focused helper functions "
                            "with single responsibilities."
                        ),
                        tags=["complexity", "maintainability"],
                    )
                )

        return findings

    def _scan_go(
        self, relative_path: str, lines: list[str], max_lines: int
    ) -> list[Finding]:
        findings: list[Finding] = []
        func_starts: list[tuple[int, str]] = []

        for lineno, line in enumerate(lines, start=1):
            if _GO_FUNC_RE.match(line):
                func_starts.append((lineno, line.strip()))

        for start_line, header in func_starts:
            depth = 0
            end_line = start_line
            started = False
            for i, line in enumerate(lines[start_line - 1 :], start=start_line):
                depth += line.count("{") - line.count("}")
                if depth > 0:
                    started = True
                if started and depth <= 0:
                    end_line = i
                    break

            func_len = end_line - start_line + 1
            if func_len > max_lines:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=start_line,
                        message=(
                            f"Function is {func_len} lines long (max {max_lines}). "
                            "Large functions are harder to test, review, and maintain."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.LOW,
                        evidence=header,
                        suggestion=(
                            "Break this function into smaller, focused helper functions "
                            "with single responsibilities."
                        ),
                        tags=["complexity", "maintainability"],
                    )
                )

        return findings

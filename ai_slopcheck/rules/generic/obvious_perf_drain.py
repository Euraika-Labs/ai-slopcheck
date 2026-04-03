from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

_PY_FOR_RE = re.compile(r"^\s+for\s+.+\s+in\s+.+:")
_PY_WHILE_RE = re.compile(r"^\s+while\s+.+:")
_JS_FOR_RE = re.compile(r"\bfor\s*[\s(]")
_JS_WHILE_RE = re.compile(r"\bwhile\s*\(")


class ObviousPerfDrainRule(Rule):
    rule_id = "obvious_perf_drain"
    title = "Nested loop creating O(n\u00b2) complexity"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.obvious_perf_drain
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        if ext == ".py":
            return self._scan_python(relative_path, content)
        else:
            return self._scan_brace(relative_path, content)

    def _scan_python(self, relative_path: str, content: str) -> list[Finding]:
        findings: list[Finding] = []
        lines = content.splitlines()

        # Track loop indent levels on a stack
        loop_indent_stack: list[int] = []

        for lineno, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if not stripped:
                continue

            current_indent = len(line) - len(stripped)

            # Pop loops that are no longer active (we dedented past them)
            while loop_indent_stack and loop_indent_stack[-1] >= current_indent:
                loop_indent_stack.pop()

            is_loop = bool(_PY_FOR_RE.match(line) or _PY_WHILE_RE.match(line))
            if is_loop:
                if loop_indent_stack:
                    # We are inside another loop — nested loop found
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=(
                                "Nested loop detected, suggesting O(n\u00b2) or worse complexity. "
                                "Consider whether a more efficient algorithm is possible."
                            ),
                            severity=Severity.NOTE,
                            confidence=Confidence.LOW,
                            evidence=stripped,
                            suggestion=(
                                "Look for opportunities to use hash maps, sets, or sorting "
                                "to reduce the algorithmic complexity."
                            ),
                            tags=["performance", "complexity"],
                        )
                    )
                loop_indent_stack.append(current_indent)

        return findings

    def _scan_brace(self, relative_path: str, content: str) -> list[Finding]:
        findings: list[Finding] = []
        lines = content.splitlines()
        loop_depth_stack: list[int] = []  # brace depth at which each loop opened
        brace_depth = 0
        reported_lines: set[int] = set()

        for lineno, line in enumerate(lines, start=1):
            opens = line.count("{")
            closes = line.count("}")

            is_loop = bool(_JS_FOR_RE.search(line) or _JS_WHILE_RE.search(line))

            if is_loop and lineno not in reported_lines:
                if loop_depth_stack:
                    reported_lines.add(lineno)
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=(
                                "Nested loop detected, suggesting O(n\u00b2) or worse complexity. "
                                "Consider whether a more efficient algorithm is possible."
                            ),
                            severity=Severity.NOTE,
                            confidence=Confidence.LOW,
                            evidence=line.strip(),
                            suggestion=(
                                "Look for opportunities to use hash maps, sets, or sorting "
                                "to reduce the algorithmic complexity."
                            ),
                            tags=["performance", "complexity"],
                        )
                    )
                # Push current brace depth (before processing braces on this line)
                loop_depth_stack.append(brace_depth + opens)

            brace_depth += opens - closes
            if brace_depth < 0:
                brace_depth = 0

            # Pop loops whose brace scope has closed
            while loop_depth_stack and loop_depth_stack[-1] > brace_depth:
                loop_depth_stack.pop()

        return findings

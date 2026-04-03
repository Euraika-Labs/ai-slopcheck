from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Go function declarations: func Name(...) ReturnType {
GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(")

# Go stub returns
GO_STUB_RETURN_RE = re.compile(
    r'^\s*return\s+(?:nil|""|0|false|true|\[\]\w+\{\}|map\[\w+\]\w+\{\})\s*$'
)

# Go empty body: just a closing brace
GO_EMPTY_BODY_RE = re.compile(r"^\s*\}\s*$")

# Go panic("not implemented") or panic("todo")
GO_PANIC_STUB_RE = re.compile(
    r'^\s*panic\(\s*"(?:not\s+implemented|todo|stub|unimplemented)',
    re.IGNORECASE,
)


class StubFunctionBodyGoRule(Rule):
    rule_id = "stub_function_body_go"
    title = "Stub function body (Go)"
    supported_extensions = {".go"}

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

        # Skip test, mock, and testdata files (Go convention)
        lower_path = relative_path.lower()
        if any(
            seg in lower_path
            for seg in ("_test.go", "_mock.go", "mock_", "/mocks/", "/testdata/")
        ):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines):
            func_match = GO_FUNC_RE.match(line)
            if func_match is None:
                continue

            func_name = func_match.group(1)
            func_line = i + 1

            # Extract brace body (Go functions always use braces)
            body_lines = self._extract_body(lines, i)
            if body_lines is None:
                continue

            if len(body_lines) == 0:
                findings.append(
                    self._make_finding(
                        relative_path, func_line, func_name, "{ }"
                    )
                )
            elif len(body_lines) == 1:
                stmt = body_lines[0].strip()
                if GO_STUB_RETURN_RE.match(stmt) or GO_PANIC_STUB_RE.match(stmt):
                    findings.append(
                        self._make_finding(
                            relative_path, func_line, func_name, stmt
                        )
                    )

        return findings

    def _make_finding(
        self,
        relative_path: str,
        line: int,
        func_name: str,
        evidence_stmt: str,
    ) -> Finding:
        return self.build_finding(
            relative_path=relative_path,
            line=line,
            message=(
                f"Function `{func_name}` has a stub body "
                f"(`{evidence_stmt[:60]}`). "
                "This may be an incomplete AI-generated implementation."
            ),
            severity=Severity.WARNING,
            confidence=Confidence.MEDIUM,
            evidence=f"{func_name}:{evidence_stmt[:60]}",
            suggestion=(
                "Implement the function body or mark it "
                "as intentionally empty."
            ),
            tags=["ai-stub", "incomplete"],
        )

    @staticmethod
    def _extract_body(lines: list[str], func_idx: int) -> list[str] | None:
        """Extract non-blank, non-comment lines from a Go function body."""
        j = func_idx
        while j < len(lines) and "{" not in lines[j]:
            j += 1
        if j >= len(lines):
            return None

        brace_depth = 0
        body: list[str] = []
        started = False

        for k in range(j, min(j + 30, len(lines))):
            for ch in lines[k]:
                if ch == "{":
                    brace_depth += 1
                    started = True
                elif ch == "}":
                    brace_depth -= 1

            if started and brace_depth == 0:
                break

            if started and brace_depth > 0 and k > j:
                stripped = lines[k].strip()
                if stripped and not stripped.startswith("//"):
                    body.append(stripped)

        return body if started else None

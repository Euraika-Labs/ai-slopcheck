from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Go error swallowing: if err != nil { return nil/""/{}/0 }
GO_ERR_SWALLOW_RE = re.compile(
    r"^\s*if\s+err\s*!=\s*nil\s*\{\s*"
    r'return\s+(?:nil|""|0|false|\[\]\w+\{\})\s*\}\s*$'
)

# Go error swallowing across lines: if err != nil { \n return nil \n }
GO_ERR_CHECK_RE = re.compile(r"^\s*if\s+err\s*!=\s*nil\s*\{")
GO_SILENT_RETURN_RE = re.compile(
    r'^\s*return\s+(?:nil|""|0|false|\[\]\w+\{\})\s*$'
)


class BareExceptPassGoRule(Rule):
    rule_id = "bare_except_pass_go"
    title = "Silent error handler (Go)"
    supported_extensions = {".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.bare_except_pass
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines):
            # Single-line pattern: if err != nil { return nil }
            if GO_ERR_SWALLOW_RE.match(line):
                findings.append(
                    self._make_finding(relative_path, i + 1, line.strip())
                )
                continue

            # Multi-line: if err != nil { \n return nil \n }
            if GO_ERR_CHECK_RE.match(line):
                body = self._extract_err_body(lines, i)
                if body is not None and len(body) == 1:
                    if GO_SILENT_RETURN_RE.match(body[0]):
                        findings.append(
                            self._make_finding(
                                relative_path, i + 1, line.strip()
                            )
                        )

        return findings

    def _make_finding(
        self, relative_path: str, line: int, evidence: str
    ) -> Finding:
        return self.build_finding(
            relative_path=relative_path,
            line=line,
            message=(
                f"Silent error handler: `{evidence[:80]}`. "
                "The error is swallowed without logging or wrapping."
            ),
            severity=Severity.WARNING,
            confidence=Confidence.MEDIUM,
            evidence=evidence[:120],
            suggestion=(
                "Log the error, wrap it with context, or return it "
                "to the caller."
            ),
            tags=["ai-error-handling", "silent-failure"],
        )

    @staticmethod
    def _extract_err_body(
        lines: list[str], if_idx: int
    ) -> list[str] | None:
        """Extract body lines from an if err != nil block."""
        brace_depth = 0
        body: list[str] = []
        started = False

        for k in range(if_idx, min(if_idx + 10, len(lines))):
            for ch in lines[k]:
                if ch == "{":
                    brace_depth += 1
                    started = True
                elif ch == "}":
                    brace_depth -= 1

            if started and brace_depth == 0:
                break

            if started and brace_depth > 0 and k > if_idx:
                stripped = lines[k].strip()
                if stripped:
                    body.append(stripped)

        return body if started else None

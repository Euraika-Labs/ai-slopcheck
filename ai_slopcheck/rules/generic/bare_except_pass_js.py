from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Matches catch clause opening (multiline form)
JS_CATCH_RE = re.compile(r"^\s*\}?\s*catch\s*(?:\([^)]*\))?\s*\{\s*$")

# Matches empty catch body: catch (...) { } on one line
JS_EMPTY_CATCH_RE = re.compile(
    r"catch\s*(?:\([^)]*\))?\s*\{\s*(?:/\*.*?\*/\s*)?\}"
)


class BareExceptPassJsRule(Rule):
    rule_id = "bare_except_pass_js"
    title = "Silent exception handler (JS/TS)"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

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
            # Check for single-line empty catch
            if JS_EMPTY_CATCH_RE.search(line):
                findings.append(
                    self._make_finding(relative_path, i + 1, line.strip())
                )
                continue

            # Check for multi-line catch with empty body
            if JS_CATCH_RE.match(line):
                body_lines = self._extract_catch_body(lines, i)
                if body_lines is not None and len(body_lines) == 0:
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
                f"Silent exception handler: `{evidence[:80]}`. "
                "Errors will be silently swallowed."
            ),
            severity=Severity.WARNING,
            confidence=Confidence.HIGH,
            evidence=evidence[:120],
            suggestion=(
                "Log the error, re-throw it, or handle it explicitly. "
                "If intentional, add a comment explaining why."
            ),
            tags=["ai-error-handling", "silent-failure"],
        )

    @staticmethod
    def _extract_catch_body(
        lines: list[str], catch_idx: int
    ) -> list[str] | None:
        """Extract non-blank, non-comment body lines from a catch block."""
        # Find the last { on the catch line — that's the catch block opener
        catch_line = lines[catch_idx]
        last_brace = catch_line.rfind("{")
        if last_brace == -1:
            return None

        # Count braces starting from the catch block's opening {
        brace_depth = 1
        body: list[str] = []

        for k in range(catch_idx + 1, min(catch_idx + 15, len(lines))):
            for ch in lines[k]:
                if ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1

            if brace_depth == 0:
                break

            stripped = lines[k].strip()
            if stripped and not stripped.startswith("//"):
                body.append(stripped)

        return body

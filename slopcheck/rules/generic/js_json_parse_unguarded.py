from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

_JSON_PARSE_RE = re.compile(r"JSON\.parse\s*\(")
_TRY_CATCH_RE = re.compile(r"\b(?:try|catch)\b")


class JsJsonParseUnguardedRule(Rule):
    rule_id = "js_json_parse_unguarded"
    title = "Unguarded JSON.parse call"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.js_json_parse_unguarded
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for lineno, line in enumerate(lines, start=1):
            if not _JSON_PARSE_RE.search(line):
                continue

            # Check 3 lines above and 3 lines below for try/catch
            start = max(0, lineno - 4)  # lineno is 1-based, so -4 gives 3 lines above
            end = min(len(lines), lineno + 3)  # 3 lines below
            context_lines = lines[start:end]

            has_guard = any(_TRY_CATCH_RE.search(ctx) for ctx in context_lines)
            if not has_guard:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "JSON.parse() called without a surrounding try/catch. "
                            "Invalid JSON input will throw a SyntaxError at runtime."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.MEDIUM,
                        evidence=evidence,
                        suggestion=(
                            "Wrap JSON.parse() in a try/catch block, or use a safe-parse "
                            "helper that returns null/undefined on failure."
                        ),
                        tags=["javascript", "error-handling"],
                    )
                )

        return findings

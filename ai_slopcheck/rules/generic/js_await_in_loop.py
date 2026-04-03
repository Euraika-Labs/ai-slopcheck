from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

_LOOP_START_RE = re.compile(r"^\s*(for\s*[\s(]|while\s*\()")
_AWAIT_RE = re.compile(r"\bawait\b")
_TEST_PATH_RE = re.compile(
    r"(?:^|[\\/])(?:test|spec|__tests__|mock|fixture)s?[\\/]|\.(?:test|spec)\."
)


class JsAwaitInLoopRule(Rule):
    rule_id = "js_await_in_loop"
    title = "Await inside loop body"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.js_await_in_loop
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        if _TEST_PATH_RE.search(relative_path):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for lineno, line in enumerate(lines, start=1):
            if not _AWAIT_RE.search(line):
                continue

            # Look up to 10 lines above for a loop start
            start = max(0, lineno - 11)
            context = lines[start : lineno - 1]
            current_indent = len(line) - len(line.lstrip())

            for ctx_line in reversed(context):
                stripped = ctx_line.lstrip()
                ctx_indent = len(ctx_line) - len(stripped)
                if ctx_indent >= current_indent:
                    continue
                if _LOOP_START_RE.match(ctx_line):
                    evidence = line.strip()
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=(
                                "Found `await` inside a loop body. Sequential awaits in loops "
                                "serialize async work and hurt performance."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.MEDIUM,
                            evidence=evidence,
                            suggestion=(
                                "Collect promises in an array and resolve them concurrently "
                                "with `Promise.all()`."
                            ),
                            tags=["javascript", "async", "performance"],
                        )
                    )
                    break
                # Stop searching once we find a less-indented non-loop line
                if ctx_indent < current_indent:
                    break

        return findings

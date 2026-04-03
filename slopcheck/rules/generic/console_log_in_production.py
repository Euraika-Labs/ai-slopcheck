from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches console.METHOD( where METHOD is captured.
_CONSOLE_RE = re.compile(r"\bconsole\.(log|warn|debug|info|error)\s*\(")

# Path segments that indicate test/fixture/mock files.
_SKIP_PATH_SEGMENTS = (
    "test", "spec", "fixture", "mock", "__mocks__",
    "script", "cli", "bin", "tool", "build", "config",
    "setup", "migration", "seed", "gulp", "webpack",
    "vite.config", "next.config", "jest.config",
    "eslint", "prettier", "babel",
    # Logger implementations intentionally wrap console.*
    "logger", "logging", "log.ts", "log.js", "log.tsx",
    "debug.ts", "debug.js",
)


class ConsoleLogInProductionRule(Rule):
    rule_id = "console_log_in_production"
    title = "console.log (or similar) left in production code"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.console_log_in_production
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        lower_path = relative_path.lower()
        if any(seg in lower_path for seg in _SKIP_PATH_SEGMENTS):
            return []

        # Build the set of methods to allow (not flag).
        allowed = {m.lower() for m in rule_config.allowed_methods}

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.lstrip()
            # Skip commented-out console statements
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            m = _CONSOLE_RE.search(line)
            if not m:
                continue
            method = m.group(1).lower()
            if method in allowed:
                continue
            evidence = m.group(0)
            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=lineno,
                    message=(
                        f"`{evidence}` found in production code. "
                        "Console logging statements should be removed before shipping "
                        "to avoid leaking internal state and cluttering browser output."
                    ),
                    severity=Severity.NOTE,
                    confidence=Confidence.MEDIUM,
                    evidence=evidence,
                    suggestion=(
                        f"Remove `{evidence}` or replace it with a proper logger "
                        "that can be disabled in production builds."
                    ),
                    tags=["console", "logging", "javascript"],
                )
            )
        return findings

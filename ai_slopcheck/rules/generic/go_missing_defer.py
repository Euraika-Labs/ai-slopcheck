from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Lines that open a closeable resource
_OPEN_RE = re.compile(
    r"(\w+)\s*,\s*\w+\s*:=\s*(?:http\.Get|os\.Open|os\.Create)\s*\("
)

# defer <var>.Body.Close() or defer <var>.Close()
_DEFER_CLOSE_RE = re.compile(r"\bdefer\s+(\w+)\.(?:Body\.)?Close\s*\(\s*\)")

# Lines that check for an error — if err != nil ends the "safe zone"

_LOOKAHEAD = 5  # number of lines to scan for a matching defer


class GoMissingDeferRule(Rule):
    rule_id = "go_missing_defer"
    title = "Resource opened without deferred Close"
    supported_extensions = {".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.go_missing_defer
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines):
            m = _OPEN_RE.search(line)
            if not m:
                continue
            var_name = m.group(1)

            # Look at the next _LOOKAHEAD lines for a defer close
            window = lines[i + 1 : i + 1 + _LOOKAHEAD]
            has_defer = any(_DEFER_CLOSE_RE.search(wl) and var_name in wl for wl in window)
            if has_defer:
                continue

            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=i + 1,
                    message=(
                        f"Resource `{var_name}` opened but no `defer {var_name}.Close()` "
                        f"found in the next {_LOOKAHEAD} lines. Resource may be leaked."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.MEDIUM,
                    evidence=line.strip(),
                    suggestion=(
                        f"Add `defer {var_name}.Body.Close()` (or `defer {var_name}.Close()`) "
                        "immediately after the error check."
                    ),
                    tags=["go", "resource-leak"],
                )
            )
        return findings

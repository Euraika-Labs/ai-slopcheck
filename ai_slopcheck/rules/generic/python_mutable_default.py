from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Matches mutable default argument: def f(x=[], def f(data={}, def f(s=set())
# Handles arbitrary preceding parameters and whitespace.
_MUTABLE_DEFAULT_RE = re.compile(
    r"^\s*def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\s*\(\s*\))"
)


class PythonMutableDefaultRule(Rule):
    rule_id = "python_mutable_default"
    title = "Mutable default argument in function definition"
    supported_extensions = {".py"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.python_mutable_default
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _MUTABLE_DEFAULT_RE.search(line)
            if m:
                mutable = m.group(1)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Mutable default argument `{mutable}` in function definition. "
                            "The same object is shared across all calls, leading to subtle bugs."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH,
                        evidence=line.strip(),
                        suggestion=(
                            f"Use `None` as the default and create a new `{mutable}` "
                            "inside the function body."
                        ),
                        tags=["python", "mutable-default"],
                    )
                )
        return findings

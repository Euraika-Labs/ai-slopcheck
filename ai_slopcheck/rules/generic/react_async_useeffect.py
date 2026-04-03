from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# useEffect(async — always a mistake; the cleanup return value is ignored
_ASYNC_USEEFFECT_RE = re.compile(r"\buseEffect\s*\(\s*async\b")


class ReactAsyncUseeffectRule(Rule):
    rule_id = "react_async_useeffect"
    title = "Async function passed directly to useEffect"
    supported_extensions = {".js", ".jsx", ".ts", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.react_async_useeffect
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _ASYNC_USEEFFECT_RE.search(line):
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "Async function passed directly to `useEffect`. "
                            "React ignores the returned Promise, so unhandled rejections "
                            "and cleanup functions will not work correctly."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.HIGH,
                        evidence=line.strip(),
                        suggestion=(
                            "Define an async function inside the effect body and call it: "
                            "`useEffect(() => { const run = async () => { ... }; run(); }, [])`."
                        ),
                        tags=["react", "async", "useeffect"],
                    )
                )
        return findings

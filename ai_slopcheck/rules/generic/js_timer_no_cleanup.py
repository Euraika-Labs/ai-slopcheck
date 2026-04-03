from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

_SET_TIMEOUT_RE = re.compile(r"\bsetTimeout\s*\(")
_SET_INTERVAL_RE = re.compile(r"\bsetInterval\s*\(")
_CLEAR_TIMEOUT_RE = re.compile(r"\bclearTimeout\s*\(")
_CLEAR_INTERVAL_RE = re.compile(r"\bclearInterval\s*\(")


class JsTimerNoCleanupRule(Rule):
    rule_id = "js_timer_no_cleanup"
    title = "Timer created in React component without cleanup"
    supported_extensions = {".jsx", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.js_timer_no_cleanup
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        has_clear_timeout = bool(_CLEAR_TIMEOUT_RE.search(content))
        has_clear_interval = bool(_CLEAR_INTERVAL_RE.search(content))

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _SET_TIMEOUT_RE.search(line) and not has_clear_timeout:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "setTimeout() used in a React component without a corresponding "
                            "clearTimeout(). This can cause state updates on unmounted components."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=evidence,
                        suggestion=(
                            "Return a cleanup function from useEffect that calls clearTimeout() "
                            "on the stored timer ID."
                        ),
                        tags=["react", "timer", "memory-leak"],
                    )
                )
            elif _SET_INTERVAL_RE.search(line) and not has_clear_interval:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "setInterval() used in a React component without a corresponding "
                            "clearInterval(). This can cause state updates on unmounted components."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=evidence,
                        suggestion=(
                            "Return a cleanup function from useEffect that calls clearInterval() "
                            "on the stored timer ID."
                        ),
                        tags=["react", "timer", "memory-leak"],
                    )
                )

        return findings

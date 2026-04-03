from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

_DANGEROUS_RE = re.compile(r"dangerouslySetInnerHTML")


class JsDangerouslySetHtmlRule(Rule):
    rule_id = "js_dangerously_set_html"
    title = "dangerouslySetInnerHTML usage detected"
    supported_extensions = {".jsx", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.js_dangerously_set_html
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _DANGEROUS_RE.search(line)
            if m:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "Raw HTML injected into the DOM via the dangerous React prop. "
                            "This is a cross-site scripting (XSS) risk."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion=(
                            "Sanitize HTML with a library like DOMPurify before passing it to "
                            "this prop, or restructure to avoid raw HTML injection entirely."
                        ),
                        tags=["react", "security", "xss"],
                    )
                )

        return findings

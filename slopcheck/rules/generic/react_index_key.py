from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches key={index}, key={i}, key={idx}, key={_index}, key={itemIndex}, etc.
_INDEX_KEY_RE = re.compile(
    r"\bkey=\{[a-z_]*(?:index|idx|i)\b[^}]*\}",
    re.IGNORECASE,
)


class ReactIndexKeyRule(Rule):
    rule_id = "react_index_key"
    title = "Array index used as React key"
    supported_extensions = {".jsx", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.react_index_key
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _INDEX_KEY_RE.search(line)
            if m:
                evidence = m.group(0)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Array index used as React key: `{evidence}`. "
                            "Index keys cause subtle bugs when the list is reordered or filtered."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion=(
                            "Use a stable, unique identifier from your data as the key "
                            "(e.g., `key={item.id}`)."
                        ),
                        tags=["react", "key-prop"],
                    )
                )
        return findings

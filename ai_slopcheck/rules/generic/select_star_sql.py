from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

_SELECT_STAR_RE = re.compile(r"SELECT\s+\*\s+FROM", re.IGNORECASE)
_TEST_PATH_RE = re.compile(
    r"(?:^|[\\/])(?:test|spec|__tests__|mock|fixture)s?[\\/]|\.(?:test|spec)\."
)


class SelectStarSqlRule(Rule):
    rule_id = "select_star_sql"
    title = "SELECT * used in SQL query"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.select_star_sql
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        if _TEST_PATH_RE.search(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _SELECT_STAR_RE.search(line)
            if m:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "SELECT * fetches all columns. This can cause performance issues "
                            "and breaks when columns are added or removed."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=evidence,
                        suggestion=(
                            "Explicitly list the columns you need "
                            "(e.g., SELECT id, name, email FROM ...)."
                        ),
                        tags=["sql", "performance", "maintainability"],
                    )
                )

        return findings

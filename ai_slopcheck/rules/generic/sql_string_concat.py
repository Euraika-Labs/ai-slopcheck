from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Two-stage detection: first check for SQL keyword, then for concatenation.
_SQL_KEYWORD_RE = re.compile(
    r"(?:SELECT|INSERT|UPDATE|DELETE|DROP)\s",
    re.IGNORECASE,
)

# Concatenation indicators on the same line as SQL.
# Each alternative requires the operator to appear *after* a closing quote so
# that bare %s placeholders inside a parameterised query are not flagged.
_CONCAT_INDICATOR_RE = re.compile(
    r"""(?:"""
    r"""["']\s*\+\s*\w"""  # "sql " + var  (concat after closing quote)
    r"""|f["'][^"']*\{[^}]+\}"""  # f"sql {var}"  (f-string)
    r"""|["'][^"'"]*['"]\s*%\s*[\w(]"""  # "sql" % var  (% after closing quote)
    r"""|["'][^"'"]*['"]\s*\.\s*format\s*\("""  # "sql".format(
    r")"
)


class SqlStringConcatRule(Rule):
    rule_id = "sql_string_concat"
    title = "SQL built by string concatenation"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.sql_string_concat
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            has_sql = _SQL_KEYWORD_RE.search(line)
            m = _CONCAT_INDICATOR_RE.search(line) if has_sql else None
            if m:
                evidence = line.strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            "SQL query built via string concatenation or interpolation. "
                            "This is a SQL injection risk."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.MEDIUM,
                        evidence=evidence,
                        suggestion=(
                            "Use parameterised queries or a query builder. "
                            "Never concatenate user input into SQL strings."
                        ),
                        tags=["sql-injection", "security"],
                    )
                )
        return findings

from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Detect nested quantifiers inside string/regex literals that could cause ReDoS.
# Patterns: (X+)+ (X*)* (X+)* (X*)+ (X|Y)+ where X itself has a quantifier
# We search for the raw pattern text inside string literals.
_NESTED_QUANT_RE = re.compile(
    r"""(?:
        \([^)]*[+*][^)]*\)[+*?]     # (a+)+ or (a+)* or (a*)+ etc.
        |
        \(\?:[^)]*[+*][^)]*\)[+*?]  # (?:a+)+ non-capturing variant
    )""",
    re.VERBOSE,
)

# Match string literal delimiters to find context
_STRING_RE = re.compile(r'(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|`[^`]*`)')


class RegexDosRule(Rule):
    rule_id = "regex_dos"
    title = "Potential ReDoS: regex with nested quantifiers"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.regex_dos
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            # Search within string literals on the line
            for string_m in _STRING_RE.finditer(line):
                literal = string_m.group(0)
                m = _NESTED_QUANT_RE.search(literal)
                if m:
                    evidence = line.strip()
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=(
                                "Regex with nested quantifiers detected. "
                                "Patterns like (a+)+ can cause catastrophic backtracking "
                                "(ReDoS) on adversarial input."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.MEDIUM,
                            evidence=evidence,
                            suggestion=(
                                "Rewrite the regex to avoid nested quantifiers. "
                                "Use possessive quantifiers or atomic groups where available, "
                                "or validate input length before applying the regex."
                            ),
                            tags=["security", "regex", "dos"],
                        )
                    )
                    break  # One finding per line is enough

        return findings

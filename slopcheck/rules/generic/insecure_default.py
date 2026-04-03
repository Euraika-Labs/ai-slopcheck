from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule


class _Pattern(NamedTuple):
    regex: re.Pattern[str]
    message: str
    suggestion: str


_PATTERNS: list[_Pattern] = [
    _Pattern(
        regex=re.compile(r"\bverify\s*=\s*False\b"),
        message="TLS certificate verification disabled (`verify=False`).",
        suggestion=(
            "Remove `verify=False`. If you need a custom CA, pass `verify='/path/to/ca.pem'`."
        ),
    ),
    _Pattern(
        regex=re.compile(r"ssl\._create_unverified_context\s*\("),
        message="Unverified SSL context created (`ssl._create_unverified_context`).",
        suggestion=(
            "Use `ssl.create_default_context()` which verifies certificates by default."
        ),
    ),
    _Pattern(
        regex=re.compile(r"\bsubprocess\b.*\bshell\s*=\s*True\b.*[^'\"]\b[a-z_]\w*\b"),
        message=(
            "subprocess with `shell=True` and variable arg"
            " — command injection risk."
        ),
        suggestion=(
            "Pass a list of arguments instead of a string, and set `shell=False` (the default)."
        ),
    ),
    _Pattern(
        regex=re.compile(r"\bDEBUG\s*=\s*True\b"),
        message="`DEBUG=True` found — must not be set in production.",
        suggestion=(
            "Set DEBUG from an environment variable: "
            "`DEBUG = os.getenv('DEBUG', 'False') == 'True'`."
        ),
    ),
    _Pattern(
        regex=re.compile(
            r"""(?:allow_origins|CORS_ORIGINS|origins)\s*[=:]\s*"""
            r"""(?:\[?\s*['"]?\*['"]?\s*\]?|['"]\*['"])"""
        ),
        message="CORS configured to allow all origins (`*`).",
        suggestion=(
            "Restrict CORS to specific trusted origins instead of using the wildcard `*`."
        ),
    ),
]


class InsecureDefaultRule(Rule):
    rule_id = "insecure_default"
    title = "Insecure configuration default"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.insecure_default
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            for pat in _PATTERNS:
                if pat.regex.search(line):
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=pat.message,
                            severity=Severity.WARNING,
                            confidence=Confidence.HIGH,
                            evidence=line.strip(),
                            suggestion=pat.suggestion,
                            tags=["insecure-default", "security"],
                        )
                    )
                    break  # one finding per line
        return findings

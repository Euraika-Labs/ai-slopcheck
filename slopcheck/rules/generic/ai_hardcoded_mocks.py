from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Common AI-generated mock data patterns
MOCK_NAME_RE = re.compile(
    r"""["'](?:John\s+Doe|Jane\s+Doe|John\s+Smith|Jane\s+Smith"""
    r"""|Bob\s+(?:Smith|Johnson|Williams)|Alice\s+(?:Smith|Johnson))["']""",
    re.IGNORECASE,
)

MOCK_COMPANY_RE = re.compile(
    r"""["'](?:Acme\s*Corp(?:oration)?|Foo\s*(?:Bar|Corp)|Example\s*(?:Corp|Inc|LLC)"""
    r"""|Test\s*(?:Corp|Company|Inc)|Widget\s*(?:Corp|Co))["']""",
    re.IGNORECASE,
)

# Default allowed email domains — RFC 2606 reserves example.com for docs/examples
_DEFAULT_ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}

MOCK_EMAIL_RE = re.compile(
    r"""["'](?:test|user|admin|info|hello|contact|john|jane)"""
    r"""(?:\.?\w*)?@([\w.-]+)["']""",
    re.IGNORECASE,
)

MOCK_PHONE_RE = re.compile(
    r"""["'](?:\+?1[-.]?)?(?:555|123)[-.]?\d{3}[-.]?\d{4}["']"""
)


class AiHardcodedMocksRule(Rule):
    rule_id = "ai_hardcoded_mocks"
    title = "AI-generated mock data in source"
    supported_extensions = None  # All file types

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.ai_hardcoded_mocks
        if not rule_config.enabled:
            return []

        # Skip test, fixture, mock, and example files
        lower_path = relative_path.lower()
        if any(
            seg in lower_path
            for seg in ("test", "fixture", "mock", "stub", "example", "spec", "seed", "sample")
        ):
            return []

        # Skip additional user-configured exclusion patterns
        from fnmatch import fnmatch

        if any(fnmatch(relative_path, p) for p in rule_config.additional_excluded_paths):
            return []

        findings: list[Finding] = []
        patterns = [
            (MOCK_NAME_RE, "mock person name"),
            (MOCK_COMPANY_RE, "mock company name"),
            (MOCK_EMAIL_RE, "mock email address"),
            (MOCK_PHONE_RE, "mock phone number"),
        ]

        for line_number, line in enumerate(content.splitlines(), start=1):
            for pattern, category in patterns:
                match = pattern.search(line)
                if match:
                    # Skip emails on allowed domains (RFC 2606)
                    if category == "mock email address":
                        domain = match.group(1).lower()
                        if domain in _DEFAULT_ALLOWED_EMAIL_DOMAINS:
                            continue
                    evidence = match.group(0).strip("\"'")
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=line_number,
                            message=(
                                f"AI-generated {category}: `{evidence}`. "
                                "This looks like placeholder mock data that should be "
                                "replaced with real values or parameterized."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.LOW,
                            evidence=evidence,
                            suggestion=(
                                f"Replace this {category} with actual data "
                                "or move it to a test fixture."
                            ),
                            tags=["ai-mock-data", "hardcoded"],
                        )
                    )
                    break  # One finding per line

        return findings

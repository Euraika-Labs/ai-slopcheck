from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.parsers.treesitter import is_in_comment
from slopcheck.rules.base import Rule

# Fake credentials and placeholder tokens — require string context (quotes)
PLACEHOLDER_CREDENTIAL_RE = re.compile(
    r"""[\"']"""
    r"(?:your|my|the|an?)[-_]?"
    r"(?:api[-_]?key|token|secret|password|credential|auth)[-_]?"
    r"(?:here|goes[-_]?here)?"
    r"""[\"']""",
    re.IGNORECASE,
)

# Explicit replacement markers
REPLACE_MARKER_RE = re.compile(
    r"(?:\bREPLACE[-_]?(?:ME|THIS|WITH)\b|<INSERT[-_][A-Z0-9_]+>|<YOUR[-_][A-Z0-9_]+>|"
    r"\bYOUR[-_][A-Z][A-Z0-9_]+[-_]HERE\b|sk[-_]xxxx|pk[-_]xxxx)",
    re.IGNORECASE,
)

# Fake URLs with placeholder domains
FAKE_URL_RE = re.compile(
    r"https?://(?:"
    r"(?:api\.)?example\.(?:com|org|net)"
    r"|your[-.][\w.-]+\.(?:com|org|io|net)"
    r"|[\w.-]*placeholder[\w.-]*\.(?:com|org|io)"
    r"|api\.yourservice\.com"
    r")",
    re.IGNORECASE,
)

# Fake file paths
FAKE_PATH_RE = re.compile(
    r"(?:path/to/(?:your|the|my)/|/path/to/(?:file|directory|config|your))",
    re.IGNORECASE,
)


class HallucinatedPlaceholderRule(Rule):
    rule_id = "hallucinated_placeholder"
    title = "Hallucinated placeholder value"
    supported_extensions = None  # All file types

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.hallucinated_placeholder
        if not rule_config.enabled:
            return []

        # Skip test and fixture files
        lower_path = relative_path.lower()
        if any(seg in lower_path for seg in ("test", "fixture", "mock", "stub", "example")):
            return []

        findings: list[Finding] = []
        patterns = [
            (PLACEHOLDER_CREDENTIAL_RE, "placeholder credential"),
            (REPLACE_MARKER_RE, "replacement marker"),
            (FAKE_URL_RE, "fake URL"),
            (FAKE_PATH_RE, "fake file path"),
        ]

        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            # Skip comment-only lines — placeholders in comments are less critical
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern, category in patterns:
                match = pattern.search(line)
                if match:
                    # Tree-sitter: skip if inside a comment
                    ext = Path(relative_path).suffix.lower()
                    ts_result = is_in_comment(
                        content, ext, line_number, match.start()
                    )
                    if ts_result is True:
                        continue
                    evidence = match.group(0)
                    # Skip allowed domains (e.g., example.com in docs)
                    if category == "fake URL" and any(
                        domain in evidence.lower()
                        for domain in rule_config.allowed_domains
                    ):
                        continue
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=line_number,
                            message=(
                                f"Hallucinated {category} found: `{evidence}`. "
                                "This is likely an AI-generated placeholder that needs "
                                "a real value."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.MEDIUM,
                            evidence=evidence,
                            suggestion=f"Replace this {category} with the actual value.",
                            tags=["ai-placeholder", "hallucinated"],
                        )
                    )
                    break  # One finding per line

        return findings

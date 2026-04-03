from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

TOKEN_TEMPLATE = r"\b({tokens})\b"


class PlaceholderTokensRule(Rule):
    rule_id = "placeholder_tokens"
    title = "Placeholder token found"
    supported_extensions = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".cs",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
    }

    def __init__(self) -> None:
        self._cached_pattern: re.Pattern[str] | None = None
        self._cached_tokens: frozenset[str] | None = None

    def _get_pattern(self, banned_tokens: list[str]) -> re.Pattern[str] | None:
        if not banned_tokens:
            return None
        token_set = frozenset(banned_tokens)
        if self._cached_pattern is not None and self._cached_tokens == token_set:
            return self._cached_pattern
        self._cached_pattern = re.compile(
            TOKEN_TEMPLATE.format(
                tokens="|".join(re.escape(token) for token in banned_tokens)
            )
        )
        self._cached_tokens = token_set
        return self._cached_pattern

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.placeholder_tokens
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        pattern = self._get_pattern(rule_config.banned_tokens)
        if pattern is None:
            return []

        findings: list[Finding] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            for match in pattern.finditer(line):
                token = match.group(1)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=line_number,
                        message=f"Found placeholder token `{token}` in source code.",
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH,
                        evidence=token,
                        suggestion="Replace the placeholder with real logic or remove it.",
                        tags=["placeholder", "cleanup"],
                    )
                )

        return findings

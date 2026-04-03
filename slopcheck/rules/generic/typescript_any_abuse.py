from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule


class _Pattern(NamedTuple):
    regex: re.Pattern[str]
    label: str
    suggestion: str


_PATTERNS: list[_Pattern] = [
    _Pattern(
        regex=re.compile(r"\bas\s+any\b"),
        label="`as any` cast",
        suggestion=(
            "Replace `as any` with a proper type assertion or use `unknown` "
            "and narrow the type with a type guard."
        ),
    ),
    _Pattern(
        regex=re.compile(r"@ts-ignore"),
        label="`@ts-ignore` suppression",
        suggestion=(
            "Fix the underlying type error instead of suppressing it. "
            "If suppression is intentional, use `@ts-expect-error` with an explanation."
        ),
    ),
    _Pattern(
        # @ts-expect-error with nothing or only whitespace after it on the same line
        regex=re.compile(r"@ts-expect-error\s*$"),
        label="`@ts-expect-error` without explanation",
        suggestion=(
            "Add a short explanation after `@ts-expect-error` "
            "so reviewers understand why the error is expected."
        ),
    ),
]


class TypescriptAnyAbuseRule(Rule):
    rule_id = "typescript_any_abuse"
    title = "TypeScript type-safety bypass"
    supported_extensions = {".ts", ".tsx"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.typescript_any_abuse
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        # Skip .d.ts declarations, @types/, and test files
        lower_path = relative_path.lower()
        if (
            relative_path.endswith(".d.ts")
            or "@types/" in lower_path
            or any(
                seg in lower_path
                for seg in ("test", "spec", "__tests__", "fixture", "mock")
            )
        ):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            for pat in _PATTERNS:
                if pat.regex.search(line):
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=lineno,
                            message=(
                                f"TypeScript type-safety bypass: {pat.label} used."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.MEDIUM,
                            evidence=line.strip(),
                            suggestion=pat.suggestion,
                            tags=["typescript", "type-safety"],
                        )
                    )
                    break  # one finding per line
        return findings

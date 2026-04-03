"""Meta-rule: flags inline suppression comments that suppress no actual finding."""
from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Finding
from slopcheck.rules.base import Rule

SUPPRESSION_RE = re.compile(
    r"(?:#|//|/\*)\s*slopcheck:\s*ignore(?:-next)?"
    r"(?:\[([^\]]*)\])?"
)


class UnusedSuppressionRule(Rule):
    rule_id = "unused_suppression"
    title = "Unused suppression comment"
    supported_extensions = None  # All file types

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        # This rule is intentionally a no-op during normal scanning.
        # It requires post-scan analysis to know which suppressions
        # were used. For now, it serves as a placeholder for the
        # unused-suppression audit feature (like ruff's RUF100).
        # Implementation will be added when the suppression system
        # tracks which directives were consumed.
        return []

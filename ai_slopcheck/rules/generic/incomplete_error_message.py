from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Generic error messages that AI generates without context.
# Only match when there's NO string interpolation (f-string, .format, %).
GENERIC_ERROR_RE = re.compile(
    r"(?:raise|throw(?:\s+new)?)\s+\w+\(\s*"
    r"[\"']("
    r"[Aa]n?\s+error\s+(?:occurred|has occurred|happened)"
    r"|[Ss]omething\s+went\s+wrong"
    r"|[Ff]ailed\s+to\s+(?:process|execute|complete|perform|handle)"
    r"|[Ii]nvalid\s+(?:input|data|request|response|parameter|argument)"
    r"|[Uu]nexpected\s+error"
    r"|[Ee]rror\s+occurred"
    r"|[Oo]peration\s+failed"
    r"|[Ii]nternal\s+(?:server\s+)?error"
    r"|[Nn]ot\s+implemented"
    r")[\"']\s*\)"
)


class IncompleteErrorMessageRule(Rule):
    rule_id = "incomplete_error_message"
    title = "Generic error message"
    supported_extensions = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go",
        ".java", ".kt", ".cs", ".rs",
    }

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.incomplete_error_message
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            # Skip lines with string interpolation — those have specifics
            if any(marker in line for marker in ("{", "%s", "%d", "f\"", "f'")):
                continue

            match = GENERIC_ERROR_RE.search(line)
            if match:
                error_msg = match.group(1)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=line_number,
                        message=(
                            f"Generic error message: `{error_msg}`. "
                            "Include specific context (what failed, why, and what to do)."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.MEDIUM,
                        evidence=error_msg,
                        suggestion=(
                            "Add context to the error message: what operation failed, "
                            "with what input, and what the caller should do about it."
                        ),
                        tags=["ai-error-message", "generic"],
                    )
                )

        return findings

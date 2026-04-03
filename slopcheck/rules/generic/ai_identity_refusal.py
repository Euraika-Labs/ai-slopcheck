from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.parsers.treesitter import is_in_non_code
from slopcheck.rules.base import Rule

# Matches AI self-identification and refusal phrases.
# These are smoking-gun indicators of unsupervised AI code commits.
AI_IDENTITY_RE = re.compile(
    r"(?:As an AI (?:language )?model|I(?:'m| am) an AI|I(?:'m| am) a language model"
    r"|I cannot (?:fulfill|provide|assist|help with|generate|create)"
    r"|I apologize,? but I (?:cannot|can't|am unable)"
    r"|I don't have (?:access to|the ability)"
    r"|This (?:is|goes) beyond (?:my|what I can)"
    r"|I'm not able to)",
    re.IGNORECASE,
)


class AiIdentityRefusalRule(Rule):
    rule_id = "ai_identity_refusal"
    title = "AI identity or refusal text in source"
    supported_extensions = None  # All file types

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.ai_identity_refusal
        if not rule_config.enabled:
            return []

        # Skip prompt templates and AI-related content files
        lower_path = relative_path.lower()
        if any(
            seg in lower_path
            for seg in ("prompt", "template", "example", "fixture", "test")
        ):
            return []

        findings: list[Finding] = []
        in_block_comment = False
        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()

            # Track block comment state (/** ... */ or /* ... */)
            if "/*" in stripped:
                in_block_comment = True
            if "*/" in stripped:
                in_block_comment = False
                continue

            # Skip comment lines — refusal text in docs/JSDoc is not committed AI
            if in_block_comment or stripped.startswith(("//", "#", "*")):
                continue

            match = AI_IDENTITY_RE.search(line)
            if match:
                # Tree-sitter: skip if inside string/comment (JSDoc, etc.)
                ext = Path(relative_path).suffix.lower()
                ts_result = is_in_non_code(
                    content, ext, line_number, match.start()
                )
                if ts_result is True:
                    continue
                evidence = match.group(0)
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=line_number,
                        message=(
                            f"AI identity/refusal text found: `{evidence}`. "
                            "This indicates unsupervised AI-generated content was committed."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion="Remove the AI-generated text and write the actual code.",
                        tags=["ai-identity", "refusal"],
                    )
                )

        return findings

from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches AI instruction-style comments left behind by code assistants.
# These phrases are distinctive of LLM output — humans write "TODO: handle X",
# LLMs write "TODO: implement the remaining logic here".
# Fixed pattern: uses a single connecting word (no unbounded repetition)
# to avoid ReDoS risk from nested quantifiers.
AI_INSTRUCTION_RE = re.compile(
    r"(?:#|//|/\*)\s*"
    r"(?:\.\.\.[\s]*)?(?:TODO:?\s*)?"
    r"(?:implement|fill|complete|finish|insert|write)"
    r"\s+(?:the\s+|your\s+|this\s+|remaining\s+|actual\s+|real\s+)?"
    r"(?:remaining\s+|actual\s+|rest\s+of\s+(?:the\s+)?)?"
    r"(?:logic|code|implementation|function|method|here|details"
    r"|functionality|body|handler|processing|algorithm)",
    re.IGNORECASE,
)

# Matches explicit code omission comments from LLMs
CODE_OMISSION_RE = re.compile(
    r"(?:#|//|/\*)\s*(?:\.\.\.[\s]*)?"
    r"(?:existing\s+code|rest\s+of\s+(?:the\s+)?(?:code|implementation|file|logic)"
    r"|remaining\s+(?:code|logic|implementation)"
    r"|omitted\s+for\s+brevity|unchanged\s+code"
    r"|code\s+goes\s+here|previous\s+code\s+(?:here|unchanged|remains)"
    r"|original\s+code|same\s+as\s+(?:before|above))",
    re.IGNORECASE,
)


class AiInstructionCommentRule(Rule):
    rule_id = "ai_instruction_comment"
    title = "AI instruction comment found"
    supported_extensions = None  # All file types

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.ai_instruction_comment
        if not rule_config.enabled:
            return []

        findings: list[Finding] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = AI_INSTRUCTION_RE.search(line) or CODE_OMISSION_RE.search(line)
            if match:
                evidence = match.group(0).strip()
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=line_number,
                        message=(
                            f"AI instruction comment found: `{evidence}`. "
                            "This appears to be an incomplete AI-generated placeholder."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion="Replace this comment with actual implementation or remove it.",
                        tags=["ai-instruction", "incomplete"],
                    )
                )

        return findings

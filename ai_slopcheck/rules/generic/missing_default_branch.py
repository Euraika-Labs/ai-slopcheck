from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Python if/elif/else detection
IF_RE = re.compile(r"^(\s*)if\s+.+:\s*$")
ELIF_RE = re.compile(r"^(\s*)elif\s+.+:\s*$")
ELSE_RE = re.compile(r"^(\s*)else\s*:\s*$")

# Python match/case detection
MATCH_RE = re.compile(r"^(\s*)match\s+.+:\s*$")
CASE_RE = re.compile(r"^(\s*)case\s+")
WILDCARD_CASE_RE = re.compile(r"^(\s*)case\s+_\s*:")


class MissingDefaultBranchRule(Rule):
    rule_id = "missing_default_branch"
    title = "Missing default branch"
    supported_extensions = {".py"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.missing_default_branch
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        lines = content.splitlines()

        findings.extend(
            self._check_if_elif_chains(lines, rule_config.min_elif_count, relative_path)
        )
        if rule_config.check_match:
            findings.extend(self._check_match_case(lines, relative_path))

        return findings

    def _check_if_elif_chains(
        self, lines: list[str], min_elif: int, relative_path: str
    ) -> list[Finding]:
        findings: list[Finding] = []
        i = 0

        while i < len(lines):
            if_match = IF_RE.match(lines[i])
            if if_match is None:
                i += 1
                continue

            if_indent = if_match.group(1)
            if_line = i + 1
            elif_count = 0
            has_else = False

            j = i + 1
            while j < len(lines):
                line = lines[j]
                stripped = line.strip()
                if not stripped:
                    j += 1
                    continue

                elif_match = ELIF_RE.match(line)
                if elif_match and elif_match.group(1) == if_indent:
                    elif_count += 1
                    j += 1
                    continue

                else_match = ELSE_RE.match(line)
                if else_match and else_match.group(1) == if_indent:
                    has_else = True
                    break

                # Check if we've moved past this if/elif chain
                line_indent = len(line) - len(line.lstrip())
                if line_indent <= len(if_indent) and not ELIF_RE.match(line):
                    break

                j += 1

            if elif_count >= min_elif and not has_else:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=if_line,
                        message=(
                            f"if/elif chain with {elif_count} branches but no `else`. "
                            "Unhandled cases may cause unexpected behavior."
                        ),
                        severity=Severity.NOTE,
                        confidence=Confidence.LOW,
                        evidence=f"if_elif_chain:{elif_count}_branches",
                        suggestion="Add an `else` branch to handle unexpected values.",
                        tags=["ai-incomplete", "missing-default"],
                    )
                )

            i = max(j, i + 1)

        return findings

    def _check_match_case(
        self, lines: list[str], relative_path: str
    ) -> list[Finding]:
        findings: list[Finding] = []
        i = 0

        while i < len(lines):
            match_match = MATCH_RE.match(lines[i])
            if match_match is None:
                i += 1
                continue

            match_indent = match_match.group(1)
            match_line = i + 1
            has_wildcard = False
            case_count = 0

            j = i + 1
            while j < len(lines):
                line = lines[j]
                stripped = line.strip()

                if not stripped:
                    j += 1
                    continue

                line_indent = len(line) - len(line.lstrip())
                if stripped and line_indent <= len(match_indent):
                    break

                if WILDCARD_CASE_RE.match(line):
                    has_wildcard = True

                if CASE_RE.match(line):
                    case_count += 1

                j += 1

            if case_count >= 2 and not has_wildcard:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=match_line,
                        message=(
                            f"match statement with {case_count} cases but no wildcard `case _:`. "
                            "Unmatched values will silently pass through."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.MEDIUM,
                        evidence=f"match_case:{case_count}_cases",
                        suggestion="Add a `case _:` wildcard branch to handle unexpected values.",
                        tags=["ai-incomplete", "missing-default"],
                    )
                )

            i = max(j, i + 1)

        return findings

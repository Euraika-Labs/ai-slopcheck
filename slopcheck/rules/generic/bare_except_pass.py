from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches bare except or except Exception (the AI pattern)
# Does NOT match specific exceptions like except KeyError — those show intent.
BROAD_EXCEPT_RE = re.compile(
    r"^\s*except\s*(?:(?:Exception|BaseException)(?:\s+as\s+\w+)?)?\s*:\s*$"
)

# Matches pass or ellipsis as the body
PASS_BODY_RE = re.compile(r"^\s*(?:pass|\.\.\.)\s*$")

# Matches a trivial comment-only line (not real handling)
COMMENT_ONLY_RE = re.compile(r"^\s*#.*$")


class BareExceptPassRule(Rule):
    rule_id = "bare_except_pass"
    title = "Silent exception handler"
    supported_extensions = {".py"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.bare_except_pass
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        lines = content.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines):
            except_match = BROAD_EXCEPT_RE.match(line)
            if except_match is None:
                continue

            except_indent = len(line) - len(line.lstrip())
            except_line = i + 1  # 1-indexed

            # Look at the body: skip blank lines and comments
            j = i + 1
            body_lines: list[str] = []
            while j < len(lines):
                body_line = lines[j]
                stripped = body_line.strip()

                # Empty line — skip
                if not stripped:
                    j += 1
                    continue

                # Dedented — end of except body
                body_indent = len(body_line) - len(body_line.lstrip())
                if body_indent <= except_indent:
                    break

                # Comment — skip (but count it if it's the only thing)
                if COMMENT_ONLY_RE.match(body_line):
                    j += 1
                    continue

                body_lines.append(stripped)
                j += 1

            # Fire if body is empty or just pass/ellipsis
            if not body_lines or (len(body_lines) == 1 and PASS_BODY_RE.match(body_lines[0])):
                except_text = line.strip()
                is_bare = "Exception" not in except_text and "BaseException" not in except_text
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=except_line,
                        message=(
                            f"Silent exception handler: `{except_text}` "
                            "with empty or pass-only body. "
                            "Errors will be silently swallowed."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH if is_bare else Confidence.MEDIUM,
                        evidence=except_text,
                        suggestion=(
                            "Log the error, re-raise it, or handle it explicitly. "
                            "If intentional, add a comment explaining why."
                        ),
                        tags=["ai-error-handling", "silent-failure"],
                    )
                )

        return findings

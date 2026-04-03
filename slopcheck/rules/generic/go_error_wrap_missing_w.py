from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches fmt.Errorf(...) calls that contain %v AND the word `err` as an argument.
# This catches the common "wrapping" pattern where %w should be used instead.
# We require `err` to appear as a standalone word after the format string
# to avoid flagging fmt.Errorf("got %v items", count) style uses.
# Only match when the last argument is exactly `err` (not errs, errorMsgs, etc.)
# This avoids FPs where %v is used with []string or other non-error types.
_ERRORF_V_RE = re.compile(
    r'fmt\.Errorf\([^)]*%v[^)]*,\s*err\s*\)'
)


class GoErrorWrapMissingWRule(Rule):
    rule_id = "go_error_wrap_missing_w"
    title = "fmt.Errorf uses %v instead of %w for error wrapping"
    supported_extensions = {".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.go_error_wrap_missing_w
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _ERRORF_V_RE.search(line)
            if not m:
                continue
            evidence = m.group(0)
            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=lineno,
                    message=(
                        f"`{evidence}` uses `%v` to include an error, but `%w` should be used "
                        "when wrapping errors so that `errors.Is` and `errors.As` can unwrap "
                        "the chain."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.HIGH,
                    evidence=evidence,
                    suggestion=(
                        "Replace `%v` with `%w` in the format string so callers can use "
                        "`errors.Is(err, target)` to inspect the error chain."
                    ),
                    tags=["go", "error-handling", "error-wrapping"],
                )
            )
        return findings

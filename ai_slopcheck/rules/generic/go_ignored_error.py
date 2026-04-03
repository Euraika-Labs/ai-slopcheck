from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Matches patterns like:
#   _ = pkg.Func(...)
#   _, _ = pkg.Func(...)
# The receiver must be a method call (pkg.Method) to reduce noise.
_IGNORED_ERROR_RE = re.compile(
    r"^\s*_\s*(?:,\s*_\s*)?=\s*(\w+\.\w+)\s*\("
)

# Intentional conventions — based on golangci-lint errcheck EXC0001
_ALLOWED_FUNCS = re.compile(
    r"^(?:"
    r"fmt\.(?:Fprint|Fprintf|Fprintln|Print|Printf|Println)"
    r"|json\.(?:NewEncoder|NewDecoder|Marshal|Unmarshal)"
    r"|io\.(?:Copy|WriteString|ReadAll)"
    r"|http\.(?:Error|Redirect|ListenAndServe)"
    r"|os\.(?:Setenv|Unsetenv|Remove|RemoveAll|Mkdir)"
    r"|\w+\.(?:Close|Flush|Write|WriteString|WriteTo"
    r"|Print|Println|Printf|Encode|Decode|Send|Emit"
    r"|Set|Del|Publish|Subscribe|Register|Unregister)"
    r"|bytes\.(?:Buffer|NewBuffer)"
    r"|strings\.(?:Builder|NewReader)"
    r"|rand\.Read|time\.Sleep"
    r"|log\.(?:Print|Printf|Println|Fatal|Fatalf)"
    r"|slog\.(?:Info|Warn|Error|Debug)"
    r")"
)


class GoIgnoredErrorRule(Rule):
    rule_id = "go_ignored_error"
    title = "Go error return silently discarded"
    supported_extensions = {".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.go_ignored_error
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        # Build extra user-configured allowlist
        extra_allowed = None
        if rule_config.extra_allowed_patterns:
            extra_allowed = re.compile(
                "|".join(rule_config.extra_allowed_patterns)
            )

        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _IGNORED_ERROR_RE.match(line)
            if not m:
                continue
            func_name = m.group(1)
            if _ALLOWED_FUNCS.match(func_name):
                continue
            if extra_allowed and extra_allowed.match(func_name):
                continue
            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=lineno,
                    message=(
                        f"Error return of `{func_name}(...)` is silently discarded. "
                        "Ignoring errors hides bugs and makes failures hard to diagnose."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.MEDIUM,
                    evidence=line.strip(),
                    suggestion=(
                        f"Capture and handle the error: `result, err := {func_name}(...); "
                        "if err != nil {{ ... }}`."
                    ),
                    tags=["go", "error-handling"],
                )
            )
        return findings

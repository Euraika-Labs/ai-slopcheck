"""Detect per-file signals of API contract breakage.

Full snapshot comparison (removed routes) is done in cli.py after the scan
because it is a cross-file concern.  This rule only emits findings for
in-file heuristics:

  1. Commented-out route decorators  (# @app.get, // app.get)
  2. @deprecated decorator on a route handler
  3. TODO or FIXME comment on the same line as a route decorator
"""
from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

# Matches a line that *starts* (possibly with whitespace/comment prefix) with a
# commented-out route decorator for Python, JS/TS or Go.
_COMMENTED_ROUTE_PY = re.compile(
    r"^\s*#\s*@(?:app|router)\.(get|post|put|delete|patch)\s*\(",
    re.IGNORECASE,
)
_COMMENTED_ROUTE_JS = re.compile(
    r"^\s*//\s*(?:app|router)\.(get|post|put|delete|patch)\s*\(",
    re.IGNORECASE,
)

# Route decorator (active) – used to check for adjacent TODO/FIXME and @deprecated
_ACTIVE_ROUTE_PY = re.compile(
    r"^\s*@(?:app|router)\.(get|post|put|delete|patch)\s*\(",
    re.IGNORECASE,
)
_ACTIVE_ROUTE_JS = re.compile(
    r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"`]",
    re.IGNORECASE,
)

# @deprecated decorator anywhere before a route handler
_DEPRECATED_DECORATOR = re.compile(r"^\s*@deprecated\b", re.IGNORECASE)

# TODO / FIXME anywhere on the same line as a route
_TODO_ON_LINE = re.compile(r"\b(TODO|FIXME)\b")


class ApiContractBreakingRule(Rule):
    rule_id = "api_contract_breaking"
    title = "Potential API contract break"
    supported_extensions = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
    }

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.api_contract_breaking
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        lines = content.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines, start=1):
            # 1. Commented-out route decorators
            if ext == ".py" and _COMMENTED_ROUTE_PY.search(line):
                findings.append(self.build_finding(
                    relative_path=relative_path,
                    line=i,
                    message=(
                        "Route decorator appears to be commented out. "
                        "This may silently remove an API endpoint."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.MEDIUM,
                    evidence=line.strip(),
                    suggestion=(
                        "Remove the route entirely or restore it. "
                        "Do not leave commented-out route decorators in production code."
                    ),
                    tags=["api-contract", "commented-route"],
                ))
                continue

            if ext in {".js", ".jsx", ".ts", ".tsx", ".go"} and _COMMENTED_ROUTE_JS.search(line):
                findings.append(self.build_finding(
                    relative_path=relative_path,
                    line=i,
                    message=(
                        "Route call appears to be commented out. "
                        "This may silently remove an API endpoint."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.MEDIUM,
                    evidence=line.strip(),
                    suggestion=(
                        "Remove the route entirely or restore it. "
                        "Do not leave commented-out route handlers in production code."
                    ),
                    tags=["api-contract", "commented-route"],
                ))
                continue

            # Detect active route lines for further checks
            is_active_route = False
            if ext == ".py" and _ACTIVE_ROUTE_PY.search(line):
                is_active_route = True
            elif ext in {".js", ".jsx", ".ts", ".tsx"} and _ACTIVE_ROUTE_JS.search(line):
                is_active_route = True

            if not is_active_route:
                continue

            # 2. @deprecated decorator on the line immediately before the route
            if i >= 2 and _DEPRECATED_DECORATOR.search(lines[i - 2]):
                findings.append(self.build_finding(
                    relative_path=relative_path,
                    line=i,
                    message=(
                        "Route handler is marked @deprecated. "
                        "Clients depending on this endpoint may break when it is removed."
                    ),
                    severity=Severity.WARNING,
                    confidence=Confidence.HIGH,
                    evidence=line.strip(),
                    suggestion=(
                        "Document the deprecation timeline and provide a migration path "
                        "before removing the route."
                    ),
                    tags=["api-contract", "deprecated-route"],
                ))
                continue

            # 3. TODO or FIXME comment on the same line as the route decorator
            todo_match = _TODO_ON_LINE.search(line)
            if todo_match:
                token = todo_match.group(1)
                findings.append(self.build_finding(
                    relative_path=relative_path,
                    line=i,
                    message=(
                        f"Route decorator has a {token} comment on the same line. "
                        "This may indicate the route is unfinished or planned for removal."
                    ),
                    severity=Severity.NOTE,
                    confidence=Confidence.LOW,
                    evidence=line.strip(),
                    suggestion=(
                        "Resolve the TODO/FIXME before shipping or remove the comment."
                    ),
                    tags=["api-contract", "todo-route"],
                ))

        return findings

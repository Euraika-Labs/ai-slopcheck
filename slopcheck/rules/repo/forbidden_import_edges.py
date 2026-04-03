from __future__ import annotations

import re
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule

IMPORT_RE = re.compile(r"^\s*import\s+([a-zA-Z0-9_.]+)")
FROM_IMPORT_RE = re.compile(r"^\s*from\s+(\.{0,3}[a-zA-Z0-9_.]*)\s+import\s+")


class ForbiddenImportEdgesRule(Rule):
    rule_id = "forbidden_import_edges"
    title = "Forbidden import edge"
    supported_extensions = {".py"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.forbidden_import_edges
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        boundaries = [
            boundary
            for boundary in rule_config.boundaries
            if fnmatch(relative_path, boundary.source_glob)
        ]
        if not boundaries:
            return []

        findings: list[Finding] = []

        for line_number, line in enumerate(content.splitlines(), start=1):
            module = self._extract_import(line, relative_path)
            if module is None:
                continue

            for boundary in boundaries:
                if any(
                    module == forbidden or module.startswith(f"{forbidden}.")
                    for forbidden in boundary.forbidden_prefixes
                ):
                    findings.append(
                        self.build_finding(
                            relative_path=relative_path,
                            line=line_number,
                            message=boundary.message,
                            severity=Severity.ERROR,
                            confidence=Confidence.HIGH,
                            evidence=module,
                            suggestion=(
                                "Route the dependency through the allowed"
                                " service or boundary."
                            ),
                            tags=["architecture", "boundary"],
                        )
                    )
                    break

        return findings

    @staticmethod
    def _resolve_relative_import(raw_module: str, relative_path: str) -> str | None:
        """Convert a relative import like '.utils' to an absolute dotted path."""
        dots = len(raw_module) - len(raw_module.lstrip("."))
        remainder = raw_module[dots:]

        parts = PurePosixPath(relative_path).with_suffix("").parts
        # __init__.py represents the package itself, not a sub-module
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if len(parts) < dots:
            return None  # relative import goes above repo root

        package_parts = parts[: len(parts) - dots]
        if remainder:
            if package_parts:
                return ".".join(package_parts) + "." + remainder
            return remainder
        return ".".join(package_parts) if package_parts else None

    @staticmethod
    def _extract_import(line: str, relative_path: str) -> str | None:
        import_match = IMPORT_RE.match(line)
        if import_match is not None:
            return import_match.group(1)

        from_import_match = FROM_IMPORT_RE.match(line)
        if from_import_match is not None:
            raw = from_import_match.group(1)
            if raw.startswith("."):
                return ForbiddenImportEdgesRule._resolve_relative_import(
                    raw, relative_path
                )
            return raw

        return None

from __future__ import annotations

import re
from collections import Counter

from ai_slopcheck.models import ScanResult

_MD_SPECIAL = re.compile(r"([\\`*_\[\]~<>|])")


def _escape_markdown(text: str) -> str:
    """Escape characters special to GitHub-Flavored Markdown."""
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return _MD_SPECIAL.sub(r"\\\1", text)


def render_summary(scan_result: ScanResult) -> str:
    lines = []
    lines.append("# slopcheck summary")
    lines.append("")
    lines.append(f"- Repository root: `{_escape_markdown(scan_result.repo_root)}`")
    lines.append(f"- Scanned files: **{scan_result.stats.scanned_files}**")
    lines.append(f"- Findings: **{scan_result.stats.findings}**")
    lines.append("")

    if not scan_result.findings:
        lines.append("No findings.")
        return "\n".join(lines)

    rule_counts = Counter(finding.rule_id for finding in scan_result.findings)
    severity_counts = Counter(finding.severity.value for finding in scan_result.findings)

    lines.append("## By severity")
    lines.append("")
    for severity, count in sorted(severity_counts.items()):
        lines.append(f"- `{severity}`: {count}")
    lines.append("")
    lines.append("## By rule")
    lines.append("")
    for rule_id, count in sorted(rule_counts.items()):
        lines.append(f"- `{rule_id}`: {count}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for finding in scan_result.findings:
        escaped_path = _escape_markdown(finding.location.path)
        lines.append(
            f"- `{escaped_path}:{finding.location.line}` "
            f"**{finding.rule_id}** — {_escape_markdown(finding.message)}"
        )

    return "\n".join(lines)

from __future__ import annotations

from ai_slopcheck.models import Finding, ScanResult, Severity


def _escape_message(value: str) -> str:
    return (
        value.replace("\x00", "")
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def _escape_property(value: str) -> str:
    return (
        value.replace("\x00", "")
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def render_annotation(finding: Finding) -> str:
    level = {
        Severity.NOTE: "notice",
        Severity.WARNING: "warning",
        Severity.ERROR: "error",
    }[finding.severity]

    properties = [
        f"file={_escape_property(finding.location.path)}",
        f"line={finding.location.line}",
        f"title={_escape_property(finding.title)}",
    ]
    if finding.location.column is not None:
        properties.append(f"col={finding.location.column}")

    return f"::{level} {','.join(properties)}::{_escape_message(finding.message)}"


def render_annotations(scan_result: ScanResult) -> str:
    return "\n".join(render_annotation(finding) for finding in scan_result.findings)

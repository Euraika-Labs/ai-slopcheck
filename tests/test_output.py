import re

from slopcheck.models import Confidence, Finding, Location, ScanResult, ScanStats, Severity
from slopcheck.output.annotations import (
    _escape_message,
    _escape_property,
    render_annotation,
    render_annotations,
)
from slopcheck.output.markdown_summary import _escape_markdown, render_summary


def _make_finding(**overrides: object) -> Finding:
    """Create a Finding with sensible defaults, applying overrides."""
    defaults: dict[str, object] = {
        "rule_id": "test_rule",
        "title": "Test finding",
        "message": "Something went wrong.",
        "severity": Severity.WARNING,
        "confidence": Confidence.HIGH,
        "location": Location(path="src/example.py", line=10),
        "fingerprint": "abc123",
        "suggestion": None,
        "evidence": "evidence-text",
        "tags": [],
    }
    defaults.update(overrides)
    return Finding(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Annotation tests
# ---------------------------------------------------------------------------


def test_render_annotation_error_severity() -> None:
    finding = _make_finding(severity=Severity.ERROR)
    output = render_annotation(finding)
    assert "::error" in output


def test_render_annotation_warning_severity() -> None:
    finding = _make_finding(severity=Severity.WARNING)
    output = render_annotation(finding)
    assert "::warning" in output


def test_render_annotation_note_severity() -> None:
    finding = _make_finding(severity=Severity.NOTE)
    output = render_annotation(finding)
    assert "::notice" in output


def test_render_annotation_includes_file_line_title() -> None:
    finding = _make_finding(
        location=Location(path="src/main.py", line=42),
        title="My title",
    )
    output = render_annotation(finding)
    assert "file=src/main.py" in output
    assert "line=42" in output
    assert "title=My title" in output


def test_render_annotation_includes_column_when_present() -> None:
    finding = _make_finding(
        location=Location(path="src/main.py", line=10, column=5),
    )
    output = render_annotation(finding)
    assert "col=5" in output


def test_render_annotation_omits_column_when_none() -> None:
    finding = _make_finding(
        location=Location(path="src/main.py", line=10, column=None),
    )
    output = render_annotation(finding)
    assert "col=" not in output


def test_escape_message_percent() -> None:
    assert _escape_message("50%") == "50%25"


def test_escape_message_newline() -> None:
    result = _escape_message("line1\nline2")
    assert "%0A" in result
    assert "\n" not in result


def test_escape_message_nul_byte() -> None:
    result = _escape_message("\x00test")
    assert "\x00" not in result
    assert "test" in result


def test_escape_property_colon_and_comma() -> None:
    result = _escape_property("a:b,c")
    assert "%3A" in result
    assert "%2C" in result
    assert ":" not in result
    assert "," not in result


def test_render_annotations_empty_findings() -> None:
    scan_result = ScanResult(
        repo_root=".",
        stats=ScanStats(scanned_files=0, findings=0),
        findings=[],
    )
    output = render_annotations(scan_result)
    assert output == ""


# ---------------------------------------------------------------------------
# Summary tests
# ---------------------------------------------------------------------------


def test_render_summary_no_findings() -> None:
    scan_result = ScanResult(
        repo_root="/repo",
        stats=ScanStats(scanned_files=5, findings=0),
        findings=[],
    )
    output = render_summary(scan_result)
    assert "No findings." in output


def test_render_summary_counts_by_severity_and_rule() -> None:
    findings = [
        _make_finding(
            rule_id="rule_a",
            severity=Severity.WARNING,
            fingerprint="fp1",
        ),
        _make_finding(
            rule_id="rule_a",
            severity=Severity.WARNING,
            fingerprint="fp2",
        ),
        _make_finding(
            rule_id="rule_b",
            severity=Severity.ERROR,
            fingerprint="fp3",
        ),
    ]
    scan_result = ScanResult(
        repo_root="/repo",
        stats=ScanStats(scanned_files=10, findings=3),
        findings=findings,
    )
    output = render_summary(scan_result)

    # Severity counts.
    assert "`warning`: 2" in output
    assert "`error`: 1" in output

    # Rule counts.
    assert "`rule_a`: 2" in output
    assert "`rule_b`: 1" in output


def test_escape_markdown_special_chars() -> None:
    result = _escape_markdown("hello `world` *bold* [link]")
    assert "\\`" in result
    assert "\\*" in result
    assert "\\[" in result
    assert "\\]" in result


def test_escape_markdown_newlines() -> None:
    result = _escape_markdown("line1\nline2\r\nline3")
    assert "\n" not in result
    assert "\r" not in result
    # Newlines become spaces.
    assert "line1 line2" in result
    assert "line2 line3" in result


# ---------------------------------------------------------------------------
# New edge-case tests
# ---------------------------------------------------------------------------


def test_escape_message_percent_ordering() -> None:
    """Percent is escaped first, so '%0A' becomes '%250A' (not double-escaped)."""
    result = _escape_message("%0A")
    assert result == "%250A"


def test_escape_property_percent_ordering() -> None:
    """Percent is escaped first, so '%3A' becomes '%253A' (not double-escaped)."""
    result = _escape_property("%3A")
    assert result == "%253A"


def test_render_annotation_full_format() -> None:
    """Rendered annotation matches the GitHub Actions workflow command pattern."""
    finding = _make_finding(
        severity=Severity.ERROR,
        location=Location(path="src/app.py", line=7),
        title="Bad import",
        message="Forbidden import detected.",
    )
    output = render_annotation(finding)
    assert re.match(r"^::(error|warning|notice) .+::.+", output)


def test_render_summary_findings_section() -> None:
    """The findings section contains the file path, line number, and rule_id."""
    finding = _make_finding(
        rule_id="placeholder_tokens",
        location=Location(path="src/foo.py", line=5),
        fingerprint="fp-summary",
    )
    scan_result = ScanResult(
        repo_root="/repo",
        stats=ScanStats(scanned_files=1, findings=1),
        findings=[finding],
    )
    output = render_summary(scan_result)

    assert "src/foo.py:5" in output
    assert "placeholder_tokens" in output

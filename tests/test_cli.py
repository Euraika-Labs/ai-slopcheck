from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ai_slopcheck.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------


def test_scan_command_writes_findings(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(output_file),
            "--fail-on",
            "none",
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    payload = output_file.read_text(encoding="utf-8")
    assert "placeholder_tokens" in payload
    assert "forbidden_import_edges" in payload


def test_summary_command_prints_markdown(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    findings_file = tmp_path / "findings.json"

    scan_result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(findings_file),
            "--fail-on",
            "none",
        ],
    )
    assert scan_result.exit_code == 0

    summary_result = runner.invoke(app, ["summary", str(findings_file)])
    assert summary_result.exit_code == 0
    assert "# slopcheck summary" in summary_result.stdout
    assert "placeholder_tokens" in summary_result.stdout


def test_create_baseline_command(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    findings_file = tmp_path / "findings.json"
    baseline_file = tmp_path / "baseline.json"

    scan_result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(findings_file),
            "--fail-on",
            "none",
        ],
    )
    assert scan_result.exit_code == 0

    baseline_result = runner.invoke(
        app,
        ["create-baseline", str(findings_file), "--output", str(baseline_file)],
    )
    assert baseline_result.exit_code == 0
    assert baseline_file.exists()


# ---------------------------------------------------------------------------
# New tests
# ---------------------------------------------------------------------------


def test_scan_exits_1_on_error_severity(tmp_path: Path) -> None:
    """Scan the sample repo without --fail-on none; default is 'error' severity.

    The sample repo has forbidden_import_edges findings at error severity,
    so the exit code should be 1.
    """
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(output_file),
        ],
    )

    # Default --fail-on is "error", and sample_repo contains error-severity findings
    assert result.exit_code == 1


def test_scan_fail_on_invalid_value_exits_nonzero() -> None:
    result = runner.invoke(
        app,
        [
            "scan",
            ".",
            "--fail-on",
            "bogus",
        ],
    )

    assert result.exit_code != 0


def test_scan_output_to_stdout(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            "-",
            "--fail-on",
            "none",
        ],
    )

    assert result.exit_code == 0

    # stdout should contain valid JSON with a "findings" key
    payload = json.loads(result.stdout)
    assert "findings" in payload
    assert "stats" in payload


def test_scan_with_baseline_suppresses_findings(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    findings_file = tmp_path / "findings.json"
    baseline_file = tmp_path / "baseline.json"

    # First scan — captures findings
    first_scan = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(findings_file),
            "--fail-on",
            "none",
        ],
    )
    assert first_scan.exit_code == 0

    # Create baseline from the first scan
    baseline_result = runner.invoke(
        app,
        ["create-baseline", str(findings_file), "--output", str(baseline_file)],
    )
    assert baseline_result.exit_code == 0

    # Second scan — with baseline, all findings should be suppressed
    second_scan = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(findings_file),
            "--baseline",
            str(baseline_file),
        ],
    )

    # With all findings suppressed, exit code should be 0
    assert second_scan.exit_code == 0


def test_github_annotations_command(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    findings_file = tmp_path / "findings.json"

    scan_result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(findings_file),
            "--fail-on",
            "none",
        ],
    )
    assert scan_result.exit_code == 0

    annotations_result = runner.invoke(
        app, ["github-annotations", str(findings_file)]
    )
    assert annotations_result.exit_code == 0

    # GitHub annotation format uses ::error or ::warning prefixes
    output = annotations_result.stdout
    assert "::error" in output or "::warning" in output


# ---------------------------------------------------------------------------
# Additional tests — threshold, config, and missing-file handling
# ---------------------------------------------------------------------------


def test_scan_fail_on_note_threshold(tmp_path: Path) -> None:
    """Scan sample_repo with --fail-on note.

    The sample repo has warning-severity placeholder_tokens findings.
    Since warning >= note in severity order, the scan must exit 1.
    """
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(output_file),
            "--fail-on",
            "note",
        ],
    )

    assert result.exit_code == 1


def test_scan_fail_on_warning_threshold_with_warnings(tmp_path: Path) -> None:
    """Scan sample_repo with --fail-on warning.

    The sample repo contains placeholder_tokens findings at warning severity,
    so exit code must be 1.
    """
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(output_file),
            "--fail-on",
            "warning",
        ],
    )

    assert result.exit_code == 1


def test_scan_fail_on_uppercase_is_accepted(tmp_path: Path) -> None:
    """--fail-on WARNING (uppercase) should be normalised and behave like lowercase.

    The sample repo has warning-severity findings, so exit code is 1.
    """
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--output",
            str(output_file),
            "--fail-on",
            "WARNING",
        ],
    )

    assert result.exit_code == 1


def test_scan_with_config_disables_rule(tmp_path: Path) -> None:
    """A custom config that disables placeholder_tokens should suppress those findings."""
    fixture_root = Path("tests/fixtures/sample_repo").resolve()
    output_file = tmp_path / "findings.json"
    config_file = tmp_path / "custom-config.yaml"

    config_file.write_text(
        "rules:\n  placeholder_tokens:\n    enabled: false\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "scan",
            str(fixture_root),
            "--repo-root",
            str(fixture_root),
            "--config",
            str(config_file),
            "--output",
            str(output_file),
            "--fail-on",
            "none",
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    rule_ids = {f["rule_id"] for f in payload["findings"]}
    assert "placeholder_tokens" not in rule_ids


def test_summary_missing_file_exits_nonzero() -> None:
    """Running summary with a nonexistent findings file should exit non-zero."""
    result = runner.invoke(app, ["summary", "/tmp/does_not_exist_findings.json"])

    assert result.exit_code != 0


def test_github_annotations_missing_file_exits_nonzero() -> None:
    """Running github-annotations with a nonexistent findings file should exit non-zero."""
    result = runner.invoke(
        app, ["github-annotations", "/tmp/does_not_exist_findings.json"]
    )

    assert result.exit_code != 0

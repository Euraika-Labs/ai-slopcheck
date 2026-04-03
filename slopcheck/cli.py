from __future__ import annotations

import sys
from pathlib import Path

import typer

from slopcheck.config import load_config
from slopcheck.engine.scanner import scan_paths
from slopcheck.models import Confidence, Finding, ScanResult, ScanStats, Severity
from slopcheck.output.annotations import render_annotations
from slopcheck.output.markdown_summary import render_summary
from slopcheck.output.sarif import render_sarif
from slopcheck.state.store import load_baseline, write_baseline

app = typer.Typer(help="Deterministic scanner for AI-style code failures.", no_args_is_help=True)

VALID_FAIL_ON = {"none", "note", "warning", "error"}
VALID_MIN_CONFIDENCE = {"low", "medium", "high"}

SEVERITY_ORDER: dict[str, int] = {"none": 0}
SEVERITY_ORDER.update({s.value: i for i, s in enumerate(Severity, start=1)})

CONFIDENCE_ORDER: dict[str, int] = {c.value: i for i, c in enumerate(Confidence, start=1)}


def _validate_fail_on(value: str) -> str:
    normalized = value.lower()
    if normalized not in VALID_FAIL_ON:
        raise typer.BadParameter(f"Must be one of: {', '.join(sorted(VALID_FAIL_ON))}")
    return normalized


def _load_scan_result(path: Path) -> ScanResult:
    try:
        return ScanResult.model_validate_json(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"slopcheck: findings file not found: {path}") from None
    except Exception as exc:
        raise SystemExit(f"slopcheck: invalid findings file {path}: {exc}") from None


def _filter_by_confidence(
    scan_result: ScanResult, min_confidence: str
) -> ScanResult:
    if min_confidence == "low":
        return scan_result
    threshold = CONFIDENCE_ORDER[min_confidence]
    filtered = [
        f for f in scan_result.findings
        if CONFIDENCE_ORDER[f.confidence.value] >= threshold
    ]
    return ScanResult(
        version=scan_result.version,
        generated_at=scan_result.generated_at,
        repo_root=scan_result.repo_root,
        stats=ScanStats(
            scanned_files=scan_result.stats.scanned_files,
            findings=len(filtered),
            rule_errors=scan_result.stats.rule_errors,
            suppressed=scan_result.stats.suppressed,
        ),
        findings=filtered,
    )


def _filter_with_baseline(scan_result: ScanResult, baseline_fingerprints: set[str]) -> ScanResult:
    if not baseline_fingerprints:
        return scan_result

    filtered = [
        finding
        for finding in scan_result.findings
        if finding.fingerprint not in baseline_fingerprints
    ]
    return ScanResult(
        version=scan_result.version,
        generated_at=scan_result.generated_at,
        repo_root=scan_result.repo_root,
        stats=ScanStats(
            scanned_files=scan_result.stats.scanned_files,
            findings=len(filtered),
            rule_errors=scan_result.stats.rule_errors,
        ),
        findings=filtered,
    )


def _write_output(payload: str, output: str) -> None:
    if output == "-":
        typer.echo(payload)
    else:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        typer.echo(f"Wrote findings to {output_path}")


def _resolve_changed_files(repo_root: Path, spec: str) -> list[Path]:
    import subprocess

    if spec.startswith("@"):
        file_path = Path(spec[1:])
        lines = file_path.read_text(encoding="utf-8").splitlines()
        return [repo_root / line.strip() for line in lines if line.strip()]
    if spec == "git":
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True, text=True, cwd=repo_root,
        )
        lines = result.stdout.strip().splitlines()
        return [repo_root / line.strip() for line in lines if line.strip()]
    raise typer.BadParameter(
        f"--changed-files must be @file.txt or 'git', got: {spec}"
    )


def _resolve_exit_code(findings: list[Finding], fail_on: str) -> int:
    if fail_on == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_on]
    should_fail = any(
        SEVERITY_ORDER[finding.severity.value] >= threshold for finding in findings
    )
    return 1 if should_fail else 0


@app.command()
def scan(
    paths: list[Path] = typer.Argument(
        None,
        help="Files or directories to scan. If omitted, scan the repo root.",
    ),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo-root",
        help="Repository root used for relative paths and config lookup.",
    ),
    config: str = typer.Option(
        "",
        "--config",
        help="Optional config file path.",
    ),
    output: str = typer.Option(
        "findings.json",
        "--output",
        help="Write findings JSON to this file. Use '-' to print JSON to stdout.",
    ),
    baseline: str = typer.Option(
        "",
        "--baseline",
        help="Optional baseline JSON file with fingerprints to suppress.",
    ),
    fail_on: str = typer.Option(
        "error",
        "--fail-on",
        callback=_validate_fail_on,
        help="Fail when a finding at or above this severity: none, note, warning, error.",
    ),
    min_confidence: str = typer.Option(
        "low",
        "--min-confidence",
        help="Only report findings at or above this confidence: low, medium, high.",
    ),
    changed_files: str = typer.Option(
        "",
        "--changed-files",
        help="Only scan changed files. Use @file.txt or 'git'.",
    ),
    jobs: int = typer.Option(
        0,
        "--jobs",
        help="Number of threads (0 = auto, 1 = sequential).",
    ),
) -> None:
    repo_root = repo_root.resolve()
    targets = list(paths) if paths else None
    config_path = Path(config) if config else None

    # Resolve changed-files into targets
    if changed_files:
        targets = _resolve_changed_files(repo_root, changed_files)
    baseline_path = Path(baseline) if baseline else None

    app_config = load_config(repo_root=repo_root, explicit_path=config_path)
    scan_result = scan_paths(
        repo_root=repo_root,
        targets=targets,
        config=app_config,
        jobs=jobs or None,
    )

    baseline_fingerprints = load_baseline(baseline_path)
    scan_result = _filter_with_baseline(scan_result, baseline_fingerprints)

    # Apply confidence filter
    normalized_conf = min_confidence.lower()
    if normalized_conf in VALID_MIN_CONFIDENCE:
        scan_result = _filter_by_confidence(scan_result, normalized_conf)

    payload = scan_result.model_dump_json(indent=2)
    _write_output(payload, output)

    exit_code = _resolve_exit_code(scan_result.findings, fail_on)

    if scan_result.stats.rule_errors > 0:
        print(
            f"slopcheck: {scan_result.stats.rule_errors} rule error(s) occurred during scan",
            file=sys.stderr,
        )

    raise typer.Exit(code=exit_code)


@app.command("summary")
def summary_command(
    findings_file: Path = typer.Argument(..., help="Path to findings JSON."),
) -> None:
    scan_result = _load_scan_result(findings_file)
    typer.echo(render_summary(scan_result))


@app.command("github-annotations")
def github_annotations(
    findings_file: Path = typer.Argument(..., help="Path to findings JSON."),
) -> None:
    scan_result = _load_scan_result(findings_file)
    typer.echo(render_annotations(scan_result))


@app.command("sarif")
def sarif_command(
    findings_file: Path = typer.Argument(..., help="Path to findings JSON."),
) -> None:
    scan_result = _load_scan_result(findings_file)
    typer.echo(render_sarif(scan_result))


@app.command("create-baseline")
def create_baseline(
    findings_file: Path = typer.Argument(..., help="Path to findings JSON."),
    output: Path = typer.Option(Path(".slopcheck/baseline.json"), "--output"),
) -> None:
    scan_result = _load_scan_result(findings_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_baseline(output, [finding.fingerprint for finding in scan_result.findings])
    typer.echo(f"Wrote baseline to {output}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.engine.repo_files import DEFAULT_CODE_EXTENSIONS, discover_files
from slopcheck.engine.suppression import is_suppressed, parse_suppressions
from slopcheck.models import Finding, ScanResult, ScanStats
from slopcheck.rules.base import Rule
from slopcheck.rules.registry import build_rules


def _build_rules_by_ext(rules: list[Rule]) -> dict[str, list[Rule]]:
    """Pre-filter: map file extensions to applicable rules."""
    by_ext: dict[str, list[Rule]] = defaultdict(list)
    for rule in rules:
        if rule.supported_extensions is None:
            for ext in DEFAULT_CODE_EXTENSIONS:
                by_ext[ext].append(rule)
        else:
            for ext in rule.supported_extensions:
                by_ext[ext].append(rule)
    return dict(by_ext)


def _scan_single_file(
    path: Path,
    repo_root: Path,
    applicable_rules: list[Rule],
    config: AppConfig,
) -> tuple[list[Finding], int, int]:
    """Scan a single file with the given rules. Thread-safe."""
    relative_path = path.relative_to(repo_root).as_posix()
    content = path.read_text(encoding="utf-8", errors="ignore")
    suppressions = parse_suppressions(content)

    findings: list[Finding] = []
    rule_errors = 0
    suppressed_count = 0

    for rule in applicable_rules:
        try:
            file_findings = rule.scan_file(
                repo_root=repo_root,
                relative_path=relative_path,
                content=content,
                config=config,
            )
            for finding in file_findings:
                if is_suppressed(
                    suppressions, finding.location.line, finding.rule_id
                ):
                    suppressed_count += 1
                else:
                    findings.append(finding)
        except Exception as exc:
            rule_errors += 1
            print(
                f"slopcheck: rule {rule.rule_id} failed on "
                f"{relative_path}: {exc}",
                file=sys.stderr,
            )

    return findings, rule_errors, suppressed_count


def scan_paths(
    *,
    repo_root: Path,
    targets: list[Path] | None,
    config: AppConfig,
    jobs: int | None = None,
) -> ScanResult:
    files = discover_files(
        repo_root=repo_root, targets=targets, ignored_patterns=config.ignored_paths
    )
    rules = build_rules()
    rules_by_ext = _build_rules_by_ext(rules)

    all_findings: list[Finding] = []
    total_errors = 0
    total_suppressed = 0

    max_workers = jobs if jobs and jobs > 0 else min(os.cpu_count() or 1, 8)

    # Build work items: (file, applicable_rules)
    work: list[tuple[Path, list[Rule]]] = []
    for path in files:
        ext = path.suffix.lower()
        applicable = rules_by_ext.get(ext, [])
        if applicable:
            work.append((path, applicable))

    if max_workers <= 1 or len(work) < 50:
        # Sequential for small batches or --jobs 1
        for path, applicable in work:
            findings, errors, suppressed = _scan_single_file(
                path, repo_root, applicable, config
            )
            all_findings.extend(findings)
            total_errors += errors
            total_suppressed += suppressed
    else:
        # Threaded for larger batches
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(
                    _scan_single_file, path, repo_root, applicable, config
                )
                for path, applicable in work
            ]
            for future in futures:
                findings, errors, suppressed = future.result()
                all_findings.extend(findings)
                total_errors += errors
                total_suppressed += suppressed

    all_findings.sort(
        key=lambda item: (
            item.location.path,
            item.location.line,
            item.rule_id,
            item.message,
        )
    )

    return ScanResult(
        repo_root=repo_root.as_posix(),
        stats=ScanStats(
            scanned_files=len(files),
            findings=len(all_findings),
            rule_errors=total_errors,
            suppressed=total_suppressed,
        ),
        findings=all_findings,
    )

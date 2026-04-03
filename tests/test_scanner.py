from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from slopcheck.config import AppConfig
from slopcheck.engine.scanner import scan_paths


def test_scan_paths_returns_correct_stats(tmp_path: Path) -> None:
    (tmp_path / "example.py").write_text("# TODO fix this\n", encoding="utf-8")
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")

    config = AppConfig()
    result = scan_paths(repo_root=tmp_path, targets=None, config=config)

    assert result.stats.scanned_files == 2
    # The placeholder_tokens rule should fire on the TODO in example.py
    assert result.stats.findings >= 1
    assert any(f.rule_id == "placeholder_tokens" for f in result.findings)


def test_scan_paths_empty_directory_returns_no_findings(tmp_path: Path) -> None:
    config = AppConfig()
    result = scan_paths(repo_root=tmp_path, targets=None, config=config)

    assert result.findings == []
    assert result.stats.scanned_files == 0
    assert result.stats.findings == 0


def test_scan_paths_ignores_configured_patterns(tmp_path: Path) -> None:
    nm_dir = tmp_path / "node_modules"
    nm_dir.mkdir()
    (nm_dir / "dep.py").write_text("# TODO should be ignored\n", encoding="utf-8")

    # Also create a non-ignored file to verify scanning still works
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

    config = AppConfig(ignored_paths=["node_modules/**"])
    result = scan_paths(repo_root=tmp_path, targets=None, config=config)

    # node_modules/dep.py should not appear in findings
    assert all("node_modules" not in f.location.path for f in result.findings)
    # main.py should still be scanned
    assert result.stats.scanned_files == 1


def test_scan_paths_rule_error_does_not_crash(tmp_path: Path) -> None:
    (tmp_path / "test.py").write_text("x = 1\n", encoding="utf-8")
    config = AppConfig()

    # Create a fake rule whose scan_file always raises
    broken_rule = MagicMock()
    broken_rule.rule_id = "broken_rule"
    broken_rule.supported_extensions = {".py"}
    broken_rule.scan_file.side_effect = RuntimeError("Simulated rule failure")

    # Patch build_rules to return only the broken rule
    with patch("slopcheck.engine.scanner.build_rules", return_value=[broken_rule]):
        result = scan_paths(repo_root=tmp_path, targets=None, config=config)

    # The scan should complete without raising
    assert result.stats.rule_errors > 0
    assert result.stats.scanned_files == 1


# ---------------------------------------------------------------------------
# Additional tests — explicit target filtering
# ---------------------------------------------------------------------------


def test_scan_paths_with_explicit_targets(tmp_path: Path) -> None:
    """When explicit targets are provided, only those files are scanned."""
    target_file = tmp_path / "example.py"
    target_file.write_text("# TODO fix this\n", encoding="utf-8")

    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n", encoding="utf-8")

    config = AppConfig()
    result = scan_paths(
        repo_root=tmp_path,
        targets=[target_file],
        config=config,
    )

    assert result.stats.scanned_files == 1
    # All findings should come from the targeted file only
    assert all(
        f.location.path == "example.py" for f in result.findings
    )
    # The placeholder_tokens rule should fire on the TODO
    assert any(f.rule_id == "placeholder_tokens" for f in result.findings)

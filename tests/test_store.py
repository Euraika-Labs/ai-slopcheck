from __future__ import annotations

import json
from pathlib import Path

import pytest

from slopcheck.state.store import load_baseline, write_baseline


def test_load_baseline_none_path_returns_empty_set() -> None:
    result = load_baseline(None)
    assert result == set()


def test_load_baseline_missing_file_returns_empty_set() -> None:
    result = load_baseline(Path("nonexistent_baseline_file.json"))
    assert result == set()


def test_load_baseline_reads_fingerprints(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps({"version": 1, "fingerprints": ["abc123", "def456"]}),
        encoding="utf-8",
    )

    result = load_baseline(baseline_file)
    assert result == {"abc123", "def456"}


def test_write_baseline_creates_file(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    write_baseline(baseline_file, ["fp1", "fp2"])

    assert baseline_file.exists()
    data = json.loads(baseline_file.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert set(data["fingerprints"]) == {"fp1", "fp2"}


def test_write_baseline_deduplicates_and_sorts(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    write_baseline(baseline_file, ["zzz", "aaa", "aaa"])

    data = json.loads(baseline_file.read_text(encoding="utf-8"))
    assert data["fingerprints"] == ["aaa", "zzz"]


def test_baseline_round_trip(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    original_fingerprints = ["alpha", "beta", "gamma"]

    write_baseline(baseline_file, original_fingerprints)
    loaded = load_baseline(baseline_file)

    assert loaded == set(original_fingerprints)


# ---------------------------------------------------------------------------
# New edge-case tests
# ---------------------------------------------------------------------------


def test_load_baseline_corrupt_json_raises_system_exit(tmp_path: Path) -> None:
    """A baseline file with invalid JSON should raise SystemExit."""
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text("not valid json", encoding="utf-8")

    with pytest.raises(SystemExit, match="invalid baseline file"):
        load_baseline(baseline_file)

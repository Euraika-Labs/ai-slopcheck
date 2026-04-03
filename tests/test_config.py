from __future__ import annotations

from pathlib import Path

import pytest

from ai_slopcheck.config import AppConfig, load_config, resolve_config_path


def test_load_config_defaults_when_no_file_exists(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert isinstance(config, AppConfig)
    assert config.rules.placeholder_tokens.enabled is True
    assert ".git/**" in config.ignored_paths


def test_load_config_from_slopcheck_dir(tmp_path: Path) -> None:
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        'ignored_paths:\n  - "vendor/**"\n',
        encoding="utf-8",
    )

    config = load_config(tmp_path)
    assert config.ignored_paths == ["vendor/**"]
    # Rules should still have defaults when not overridden
    assert config.rules.placeholder_tokens.enabled is True


def test_load_config_explicit_path_overrides_discovery(tmp_path: Path) -> None:
    # Create a discoverable config that should NOT be used
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    discoverable = config_dir / "config.yaml"
    discoverable.write_text(
        'ignored_paths:\n  - "discoverable/**"\n',
        encoding="utf-8",
    )

    # Create an explicit config that SHOULD be used
    explicit = tmp_path / "my-config.yaml"
    explicit.write_text(
        'ignored_paths:\n  - "explicit/**"\n',
        encoding="utf-8",
    )

    config = load_config(tmp_path, explicit_path=explicit)
    assert config.ignored_paths == ["explicit/**"]


def test_load_config_disabled_placeholder_tokens(tmp_path: Path) -> None:
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "rules:\n  placeholder_tokens:\n    enabled: false\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path)
    assert config.rules.placeholder_tokens.enabled is False


def test_load_config_empty_yaml_returns_defaults(tmp_path: Path) -> None:
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("", encoding="utf-8")

    config = load_config(tmp_path)
    assert isinstance(config, AppConfig)
    assert config.rules.placeholder_tokens.enabled is True
    assert ".git/**" in config.ignored_paths


def test_load_config_malformed_yaml_raises_system_exit(tmp_path: Path) -> None:
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("{{bad yaml", encoding="utf-8")

    with pytest.raises(SystemExit, match="invalid YAML"):
        load_config(tmp_path)


def test_resolve_config_path_prefers_slopcheck_dir(tmp_path: Path) -> None:
    # Create both candidates — .slopcheck/config.yaml should win
    slopcheck_dir = tmp_path / ".slopcheck"
    slopcheck_dir.mkdir()
    preferred = slopcheck_dir / "config.yaml"
    preferred.write_text("# preferred\n", encoding="utf-8")

    fallback = tmp_path / ".slopcheck.yaml"
    fallback.write_text("# fallback\n", encoding="utf-8")

    resolved = resolve_config_path(tmp_path, explicit_path=None)
    assert resolved == preferred


# ---------------------------------------------------------------------------
# New edge-case tests
# ---------------------------------------------------------------------------


def test_load_config_slopcheck_yaml_dotfile(tmp_path: Path) -> None:
    """resolve_config_path discovers a bare .slopcheck.yaml file."""
    config_file = tmp_path / ".slopcheck.yaml"
    config_file.write_text(
        'ignored_paths:\n  - "dotfile/**"\n',
        encoding="utf-8",
    )

    resolved = resolve_config_path(tmp_path, explicit_path=None)
    assert resolved == config_file


def test_load_config_slopcheck_yml_dotfile(tmp_path: Path) -> None:
    """resolve_config_path discovers a bare .slopcheck.yml file."""
    config_file = tmp_path / ".slopcheck.yml"
    config_file.write_text(
        'ignored_paths:\n  - "yml-dotfile/**"\n',
        encoding="utf-8",
    )

    resolved = resolve_config_path(tmp_path, explicit_path=None)
    assert resolved == config_file


def test_load_config_nonexistent_explicit_path_raises(tmp_path: Path) -> None:
    """Passing an explicit path that does not exist raises FileNotFoundError."""
    missing = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(tmp_path, explicit_path=missing)


def test_load_config_invalid_structure_raises_system_exit(tmp_path: Path) -> None:
    """Valid YAML with wrong types raises SystemExit via Pydantic validation."""
    config_dir = tmp_path / ".slopcheck"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "rules:\n  placeholder_tokens:\n    enabled: not-a-bool\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="invalid config"):
        load_config(tmp_path)

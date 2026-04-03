from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, MissingDefaultBranchConfig
from slopcheck.rules.generic.missing_default_branch import MissingDefaultBranchRule


def _make_config() -> AppConfig:
    config = AppConfig()
    config.rules.missing_default_branch = MissingDefaultBranchConfig(enabled=True)
    return config


def _scan(content: str) -> list:
    rule = MissingDefaultBranchRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/handler.py",
        content=content,
        config=_make_config(),
    )


def test_detects_if_elif_without_else():
    code = (
        "if status == 'active':\n"
        "    return 'Running'\n"
        "elif status == 'paused':\n"
        "    return 'Paused'\n"
        "elif status == 'stopped':\n"
        "    return 'Stopped'\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert "if/elif" in findings[0].message


def test_ignores_if_elif_with_else():
    code = (
        "if status == 'active':\n"
        "    return 'Running'\n"
        "elif status == 'paused':\n"
        "    return 'Paused'\n"
        "elif status == 'stopped':\n"
        "    return 'Stopped'\n"
        "else:\n"
        "    return 'Unknown'\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_simple_if_elif():
    code = (
        "if x > 0:\n"
        "    return 'positive'\n"
        "elif x < 0:\n"
        "    return 'negative'\n"
    )
    findings = _scan(code)
    # Only 1 elif — below default threshold of 2
    assert len(findings) == 0


def test_detects_match_without_wildcard():
    code = (
        "match command:\n"
        "    case 'start':\n"
        "        start()\n"
        "    case 'stop':\n"
        "        stop()\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert "match" in findings[0].message


def test_ignores_match_with_wildcard():
    code = (
        "match command:\n"
        "    case 'start':\n"
        "        start()\n"
        "    case 'stop':\n"
        "        stop()\n"
        "    case _:\n"
        "        unknown()\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_configurable_min_elif():
    from slopcheck.config import MissingDefaultBranchConfig

    config = AppConfig()
    config.rules.missing_default_branch = MissingDefaultBranchConfig(
        enabled=True, min_elif_count=1
    )
    code = (
        "if x > 0:\n"
        "    return 'pos'\n"
        "elif x < 0:\n"
        "    return 'neg'\n"
    )
    rule = MissingDefaultBranchRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/handler.py",
        content=code,
        config=config,
    )
    assert len(findings) == 1


def test_skips_non_python():
    rule = MissingDefaultBranchRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.go",
        content="if x > 0 {\n} else if x < 0 {\n}\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_check_match_disabled():
    # With check_match=False, a match without case _ must NOT produce a finding
    from slopcheck.config import MissingDefaultBranchConfig

    config = AppConfig()
    config.rules.missing_default_branch = MissingDefaultBranchConfig(check_match=False)
    code = (
        "match command:\n"
        "    case 'start':\n"
        "        start()\n"
        "    case 'stop':\n"
        "        stop()\n"
    )
    rule = MissingDefaultBranchRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/handler.py",
        content=code,
        config=config,
    )
    assert len(findings) == 0


def test_nested_if_elif():
    # Nested if/elif chain: only the outer one (with enough branches) should fire
    code = (
        "if status == 'active':\n"
        "    if x > 0:\n"
        "        pass\n"
        "    elif x < 0:\n"
        "        pass\n"
        "elif status == 'paused':\n"
        "    pass\n"
        "elif status == 'stopped':\n"
        "    pass\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].location.line == 1

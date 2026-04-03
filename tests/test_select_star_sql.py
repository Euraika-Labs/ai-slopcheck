from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, SelectStarSqlConfig
from slopcheck.rules.generic.select_star_sql import SelectStarSqlRule


def _scan(content: str, path: str = "src/repo.py") -> list:
    rule = SelectStarSqlRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_select_star_python() -> None:
    code = 'sql = "SELECT * FROM users"\n'
    findings = _scan(code)
    assert len(findings) == 1
    assert "SELECT" in findings[0].evidence


def test_detects_select_star_case_insensitive() -> None:
    code = 'query = "select * from orders"\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_allows_explicit_columns() -> None:
    code = 'sql = "SELECT id, name, email FROM users"\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_select_star_in_ts() -> None:
    code = "const q = `SELECT * FROM products`;\n"
    findings = _scan(code, path="src/db.ts")
    assert len(findings) == 1


def test_skips_test_files() -> None:
    code = 'sql = "SELECT * FROM users"\n'
    findings = _scan(code, path="tests/test_repo.py")
    assert len(findings) == 0


def test_detects_in_go_file() -> None:
    code = 'query := "SELECT * FROM sessions"\n'
    findings = _scan(code, path="src/store.go")
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.select_star_sql = SelectStarSqlConfig(enabled=False)
    rule = SelectStarSqlRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/repo.py",
        content='sql = "SELECT * FROM users"\n',
        config=config,
    )
    assert len(findings) == 0

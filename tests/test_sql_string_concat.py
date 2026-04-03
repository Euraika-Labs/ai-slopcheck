from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, SqlStringConcatConfig
from ai_slopcheck.rules.generic.sql_string_concat import SqlStringConcatRule


def _scan(content: str, path: str = "src/db.py") -> list:
    rule = SqlStringConcatRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_select_plus_var() -> None:
    code = 'query = "SELECT * FROM users WHERE id = " + user_id\n'
    findings = _scan(code)
    assert len(findings) == 1
    assert "SQL injection" in findings[0].message


def test_detects_fstring_interpolation() -> None:
    code = 'query = f"SELECT * FROM users WHERE name = {name}"\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_percent_format() -> None:
    code = 'query = "SELECT * FROM orders WHERE id = %s" % order_id\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_insert_concat() -> None:
    code = 'q = "INSERT INTO logs VALUES (" + data + ")"\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_delete_concat() -> None:
    code = 'q = "DELETE FROM sessions WHERE token = " + tok\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_safe_parameterised_query() -> None:
    code = 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_plain_string_no_interpolation() -> None:
    code = 'query = "SELECT * FROM users"\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_matching_extension() -> None:
    rule = SqlStringConcatRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="README.md",
        content='q = "SELECT * FROM t WHERE id = " + x\n',
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.sql_string_concat = SqlStringConcatConfig(enabled=False)
    rule = SqlStringConcatRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/db.py",
        content='q = "SELECT * FROM t WHERE id = " + x\n',
        config=config,
    )
    assert len(findings) == 0


def test_multiple_violations() -> None:
    code = (
        'q1 = "SELECT * FROM a WHERE x = " + x\n'
        'q2 = f"UPDATE b SET y = {y}"\n'
    )
    findings = _scan(code)
    assert len(findings) == 2

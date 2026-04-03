from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, JsLooseEqualityConfig
from slopcheck.rules.generic.js_loose_equality import JsLooseEqualityRule


def _scan(content: str, path: str = "src/util.ts") -> list:
    rule = JsLooseEqualityRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_loose_double_equal() -> None:
    code = "if (x == 0) {\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_loose_not_equal() -> None:
    code = "if (x != null) {\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_allows_strict_triple_equal() -> None:
    code = "if (x === 0) {\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_strict_not_equal() -> None:
    code = "if (x !== null) {\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_comment_lines() -> None:
    code = "// if (x == 0) this would fire\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_in_js_file() -> None:
    code = "return a == b;\n"
    findings = _scan(code, path="src/compare.js")
    assert len(findings) == 1


def test_skips_non_js_ts_files() -> None:
    rule = JsLooseEqualityRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/code.py",
        content="if x == 0:\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.js_loose_equality = JsLooseEqualityConfig(enabled=False)
    rule = JsLooseEqualityRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/util.ts",
        content="if (x == 0) {\n",
        config=config,
    )
    assert len(findings) == 0

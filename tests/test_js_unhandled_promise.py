from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, JsUnhandledPromiseConfig
from ai_slopcheck.rules.generic.js_unhandled_promise import JsUnhandledPromiseRule


def _scan(content: str, path: str = "src/api.ts") -> list:
    rule = JsUnhandledPromiseRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_then_without_catch() -> None:
    code = "fetch('/api').then(res => res.json());\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert ".then" in findings[0].evidence


def test_detects_multiline_then_without_catch() -> None:
    code = """\
fetch('/api')
  .then(res => res.json())
  .then(data => console.log(data));
"""
    findings = _scan(code)
    assert len(findings) >= 1


def test_allows_then_with_catch_on_same_line() -> None:
    code = "fetch('/api').then(r => r.json()).catch(err => console.error(err));\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_then_with_catch_nearby() -> None:
    code = """\
fetch('/api')
  .then(res => res.json())
  .catch(err => handleError(err));
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_js_ts_files() -> None:
    rule = JsUnhandledPromiseRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/api.py",
        content="fetch('/api').then(r => r)\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_detects_in_jsx_file() -> None:
    code = "loadData().then(setData);\n"
    findings = _scan(code, path="src/App.jsx")
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.js_unhandled_promise = JsUnhandledPromiseConfig(enabled=False)
    rule = JsUnhandledPromiseRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/api.ts",
        content="fetch('/api').then(r => r.json());\n",
        config=config,
    )
    assert len(findings) == 0

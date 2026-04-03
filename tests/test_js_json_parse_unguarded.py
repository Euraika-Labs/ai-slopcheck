from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, JsJsonParseUnguardedConfig
from slopcheck.rules.generic.js_json_parse_unguarded import JsJsonParseUnguardedRule


def _scan(content: str, path: str = "src/parser.ts") -> list:
    rule = JsJsonParseUnguardedRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_unguarded_json_parse() -> None:
    code = "const data = JSON.parse(raw);\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "JSON.parse" in findings[0].evidence


def test_detects_unguarded_in_function() -> None:
    code = """\
function parse(raw) {
    const obj = JSON.parse(raw);
    return obj;
}
"""
    findings = _scan(code)
    assert len(findings) == 1


def test_allows_json_parse_inside_try() -> None:
    code = """\
try {
    const data = JSON.parse(raw);
} catch (e) {
    console.error(e);
}
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_json_parse_with_catch_nearby() -> None:
    code = """\
try {
    doSomething();
    const data = JSON.parse(raw);
} catch (err) {
    handle(err);
}
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_json_parse_with_catch_below() -> None:
    code = """\
try {
const data = JSON.parse(raw);
} catch(e) {}
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_js_ts_files() -> None:
    rule = JsJsonParseUnguardedRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/parser.py",
        content="data = JSON.parse(raw)\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_detects_in_js_file() -> None:
    code = "const x = JSON.parse(input);\n"
    findings = _scan(code, path="src/util.js")
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.js_json_parse_unguarded = JsJsonParseUnguardedConfig(enabled=False)
    rule = JsJsonParseUnguardedRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/parser.ts",
        content="const data = JSON.parse(raw);\n",
        config=config,
    )
    assert len(findings) == 0

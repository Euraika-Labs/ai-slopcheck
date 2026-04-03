from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, DeepNestingConfig
from ai_slopcheck.rules.generic.deep_nesting import DeepNestingRule


def _make_config() -> AppConfig:
    config = AppConfig()
    config.rules.deep_nesting = DeepNestingConfig(enabled=True, max_depth=4)
    return config


def _scan(content: str, path: str = "src/logic.py") -> list:
    rule = DeepNestingRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=_make_config(),
    )


def test_detects_deep_python_nesting() -> None:
    code = """\
def foo():
    if a:
        for x in y:
            if b:
                while c:
                    do_something()
"""
    findings = _scan(code)
    assert len(findings) >= 1


def test_allows_shallow_python_nesting() -> None:
    code = """\
def foo():
    if a:
        return b
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_deep_js_nesting() -> None:
    code = """\
function foo() {
    if (a) {
        for (const x of y) {
            if (b) {
                while (c) {
                    doSomething();
                }
            }
        }
    }
}
"""
    findings = _scan(code, path="src/logic.ts")
    assert len(findings) >= 1


def test_allows_shallow_js_nesting() -> None:
    code = """\
function foo() {
    if (a) {
        return b;
    }
}
"""
    findings = _scan(code, path="src/logic.ts")
    assert len(findings) == 0


def test_custom_max_depth() -> None:
    config = AppConfig()
    config.rules.deep_nesting = DeepNestingConfig(enabled=True, max_depth=2)
    rule = DeepNestingRule()
    code = """\
def foo():
    if a:
        if b:
            return c
"""
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/logic.py",
        content=code,
        config=config,
    )
    assert len(findings) >= 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.deep_nesting = DeepNestingConfig(enabled=False)
    rule = DeepNestingRule()
    code = "                    deeply_nested_call()\n"
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/logic.py",
        content=code,
        config=config,
    )
    assert len(findings) == 0

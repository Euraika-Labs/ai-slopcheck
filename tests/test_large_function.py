from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, LargeFunctionConfig
from slopcheck.rules.generic.large_function import LargeFunctionRule


def _make_config(max_lines: int = 60) -> AppConfig:
    config = AppConfig()
    config.rules.large_function = LargeFunctionConfig(
        enabled=True, max_lines=max_lines
    )
    return config


def _scan(content: str, path: str = "src/service.py") -> list:
    rule = LargeFunctionRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=_make_config(),
    )


def _make_py_func(n_lines: int) -> str:
    body = "\n".join(f"    x = {i}" for i in range(n_lines))
    return f"def big_func():\n{body}\n"


def _make_js_func(n_lines: int) -> str:
    body = "\n".join(f"    const x{i} = {i};" for i in range(n_lines))
    return f"function bigFunc() {{\n{body}\n}}\n"


def test_detects_large_python_function() -> None:
    code = _make_py_func(70)
    findings = _scan(code)
    assert len(findings) >= 1
    assert findings[0].rule_id == "large_function"


def test_allows_small_python_function() -> None:
    code = _make_py_func(10)
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_large_js_function() -> None:
    code = _make_js_func(70)
    findings = _scan(code, path="src/service.ts")
    assert len(findings) >= 1


def test_allows_small_js_function() -> None:
    code = _make_js_func(10)
    findings = _scan(code, path="src/service.ts")
    assert len(findings) == 0


def test_custom_max_lines() -> None:
    config = AppConfig()
    config.rules.large_function = LargeFunctionConfig(enabled=True, max_lines=20)
    rule = LargeFunctionRule()
    code = _make_py_func(25)
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.py",
        content=code,
        config=config,
    )
    assert len(findings) >= 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.large_function = LargeFunctionConfig(enabled=False)
    rule = LargeFunctionRule()
    code = _make_py_func(100)
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.py",
        content=code,
        config=config,
    )
    assert len(findings) == 0

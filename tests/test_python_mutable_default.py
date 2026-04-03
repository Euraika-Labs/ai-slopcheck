from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, PythonMutableDefaultConfig
from ai_slopcheck.rules.generic.python_mutable_default import PythonMutableDefaultRule


def _scan(content: str, path: str = "src/utils.py") -> list:
    rule = PythonMutableDefaultRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_empty_list_default() -> None:
    findings = _scan("def process(items=[]):\n    return items\n")
    assert len(findings) == 1
    assert "[]" in findings[0].message


def test_detects_empty_dict_default() -> None:
    findings = _scan("def configure(data={}):\n    return data\n")
    assert len(findings) == 1
    assert "{}" in findings[0].message


def test_detects_set_default() -> None:
    findings = _scan("def collect(seen=set()):\n    return seen\n")
    assert len(findings) == 1
    assert "set()" in findings[0].message


def test_safe_none_default() -> None:
    findings = _scan("def process(items=None):\n    if items is None:\n        items = []\n")
    assert len(findings) == 0


def test_safe_immutable_default() -> None:
    findings = _scan("def greet(name='world'):\n    return f'Hello {name}'\n")
    assert len(findings) == 0


def test_safe_tuple_default() -> None:
    findings = _scan("def apply(ops=()):\n    return ops\n")
    assert len(findings) == 0


def test_skips_non_python() -> None:
    rule = PythonMutableDefaultRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/utils.js",
        content="function process(items=[]) { return items; }\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.python_mutable_default = PythonMutableDefaultConfig(enabled=False)
    rule = PythonMutableDefaultRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/utils.py",
        content="def process(items=[]):\n    return items\n",
        config=config,
    )
    assert len(findings) == 0


def test_multiple_mutable_defaults() -> None:
    code = "def f(a=[], b={}):\n    pass\n"
    findings = _scan(code)
    # The regex matches the first mutable found on the line; one finding per line
    assert len(findings) == 1

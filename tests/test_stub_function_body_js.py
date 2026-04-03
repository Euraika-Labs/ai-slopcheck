from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.stub_function_body_js import StubFunctionBodyJsRule


def _scan(content: str, path: str = "src/service.ts") -> list:
    rule = StubFunctionBodyJsRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_function_return_null():
    code = "function getData() {\n  return null;\n}\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "getData" in findings[0].message


def test_detects_arrow_return_null():
    code = "const getData = () => null;\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_arrow_return_empty_array():
    code = "const getItems = () => [];\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_empty_function_body():
    code = "function handler() { }\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_return_undefined():
    code = "function process() {\n  return undefined;\n}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_real_implementation():
    code = "function getData() {\n  const result = fetch(url);\n  return result;\n}\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_non_js_files():
    code = "function getData() {\n  return null;\n}\n"
    findings = _scan(code, path="src/main.py")
    assert len(findings) == 0


def test_detects_async_arrow():
    code = "const fetchData = async () => null;\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_export_function():
    code = "export function getUser() {\n  return null;\n}\n"
    findings = _scan(code)
    assert len(findings) == 1

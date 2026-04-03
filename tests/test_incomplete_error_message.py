from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.incomplete_error_message import IncompleteErrorMessageRule


def _scan(content: str, path: str = "src/service.py") -> list:
    rule = IncompleteErrorMessageRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_an_error_occurred():
    findings = _scan('raise ValueError("An error occurred")\n')
    assert len(findings) == 1


def test_detects_something_went_wrong():
    findings = _scan('raise RuntimeError("Something went wrong")\n')
    assert len(findings) == 1


def test_detects_invalid_input():
    findings = _scan('raise ValueError("Invalid input")\n')
    assert len(findings) == 1


def test_detects_operation_failed():
    findings = _scan('raise Exception("Operation failed")\n')
    assert len(findings) == 1


def test_ignores_specific_error():
    findings = _scan(
        'raise ValueError("User ID must be a positive integer")\n'
    )
    assert len(findings) == 0


def test_ignores_f_string_error():
    findings = _scan(
        'raise ValueError(f"Failed to process {item}")\n'
    )
    assert len(findings) == 0


def test_ignores_format_string():
    findings = _scan(
        'raise ValueError("Invalid input: %s" % data)\n'
    )
    assert len(findings) == 0


def test_skips_non_raise_lines():
    findings = _scan('message = "An error occurred"\n')
    assert len(findings) == 0


def test_detects_throw_new():
    findings = _scan(
        'throw new Error("Something went wrong")\n',
        path="src/service.ts",
    )
    assert len(findings) == 1


def test_skips_unsupported_extension():
    rule = IncompleteErrorMessageRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.h",
        content='throw new Error("Something went wrong")\n',
        config=AppConfig(),
    )
    assert len(findings) == 0

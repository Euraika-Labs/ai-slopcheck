from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.bare_except_pass_go import BareExceptPassGoRule


def _scan(content: str) -> list:
    rule = BareExceptPassGoRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="pkg/service.go",
        content=content,
        config=AppConfig(),
    )


def test_detects_err_return_nil_oneline():
    code = "if err != nil { return nil }\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_err_return_nil_multiline():
    code = "if err != nil {\n\treturn nil\n}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_err_return_empty_string():
    code = 'if err != nil {\n\treturn ""\n}\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_err_with_logging():
    code = (
        "if err != nil {\n"
        "\tlog.Error(err)\n"
        "\treturn nil\n"
        "}\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_err_return_err():
    code = "if err != nil {\n\treturn err\n}\n"
    # "return err" doesn't match GO_SILENT_RETURN_RE
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_non_go():
    rule = BareExceptPassGoRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.py",
        content="if err != nil { return nil }\n",
        config=AppConfig(),
    )
    assert len(findings) == 0

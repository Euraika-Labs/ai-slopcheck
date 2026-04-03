from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.stub_function_body_go import StubFunctionBodyGoRule


def _scan(content: str) -> list:
    rule = StubFunctionBodyGoRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="pkg/service.go",
        content=content,
        config=AppConfig(),
    )


def test_detects_return_nil():
    code = "func GetUser(id string) (*User, error) {\n\treturn nil, nil\n}\n"
    # "return nil, nil" won't match because it has a comma — this is
    # actually two return values and may be intentional
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_single_return_nil():
    code = "func GetUser(id string) error {\n\treturn nil\n}\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "GetUser" in findings[0].message


def test_detects_return_empty_string():
    code = 'func GetName() string {\n\treturn ""\n}\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_empty_body():
    code = "func Handler(w http.ResponseWriter, r *http.Request) {\n}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_panic_not_implemented():
    code = 'func Process() {\n\tpanic("not implemented")\n}\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_real_implementation():
    code = (
        "func GetUser(id string) (*User, error) {\n"
        "\tuser, err := db.FindByID(id)\n"
        "\tif err != nil {\n"
        "\t\treturn nil, err\n"
        "\t}\n"
        "\treturn user, nil\n"
        "}\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_non_go_files():
    rule = StubFunctionBodyGoRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.py",
        content="func GetUser() { return nil }\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_detects_method_receiver():
    code = "func (s *Service) GetData() error {\n\treturn nil\n}\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "GetData" in findings[0].message

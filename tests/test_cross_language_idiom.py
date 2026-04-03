from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, CrossLanguageIdiomConfig
from slopcheck.rules.generic.cross_language_idiom import CrossLanguageIdiomRule


def _scan(content: str, path: str) -> list:
    rule = CrossLanguageIdiomRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


# ---------------------------------------------------------------------------
# Python file tests
# ---------------------------------------------------------------------------

def test_py_detects_push() -> None:
    findings = _scan("self.items.push(new_item)\n", path="app.py")
    assert len(findings) == 1
    assert "push" in findings[0].evidence


def test_py_detects_null() -> None:
    findings = _scan("value = null\n", path="utils.py")
    assert len(findings) == 1
    assert "null" in findings[0].evidence


def test_py_detects_console_log() -> None:
    findings = _scan("console.log('debug')\n", path="script.py")
    assert len(findings) == 1
    assert "console.log" in findings[0].evidence


def test_py_does_not_flag_none() -> None:
    findings = _scan("value = None\n", path="app.py")
    assert len(findings) == 0


def test_py_skips_null_inside_string() -> None:
    # `null` inside a string literal should not be flagged.
    findings = _scan('msg = "got null response"\n', path="app.py")
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# JS/TS file tests
# ---------------------------------------------------------------------------

def test_js_detects_nil() -> None:
    findings = _scan("if (value === nil) return;\n", path="src/util.js")
    assert len(findings) == 1
    assert "nil" in findings[0].evidence


def test_ts_detects_def_keyword() -> None:
    findings = _scan("def myFunction(x) {\n", path="src/service.ts")
    assert len(findings) == 1
    assert "def" in findings[0].evidence


def test_jsx_detects_elif() -> None:
    findings = _scan("} elif (condition) {\n", path="Component.jsx")
    assert len(findings) == 1
    assert "elif" in findings[0].evidence


def test_tsx_detects_go_short_assign() -> None:
    findings = _scan("    x := 42\n", path="App.tsx")
    assert len(findings) == 1
    assert ":=" in findings[0].evidence


def test_js_does_not_flag_null() -> None:
    findings = _scan("const x = null;\n", path="index.js")
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# Go file tests
# ---------------------------------------------------------------------------

def test_go_detects_none() -> None:
    findings = _scan("var x = None\n", path="main.go")
    assert len(findings) == 1
    assert "None" in findings[0].evidence


def test_go_detects_self_dot() -> None:
    findings = _scan("    self.value = 42\n", path="handler.go")
    assert len(findings) == 1
    assert "self." in findings[0].evidence


def test_go_detects_this_dot() -> None:
    findings = _scan("    this.name = name\n", path="service.go")
    assert len(findings) == 1
    assert "this." in findings[0].evidence


def test_go_detects_console_log() -> None:
    findings = _scan("    console.log(result)\n", path="main.go")
    assert len(findings) == 1
    assert "console.log" in findings[0].evidence


def test_go_does_not_flag_nil() -> None:
    findings = _scan("    if err != nil {\n", path="main.go")
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# Common behaviour tests
# ---------------------------------------------------------------------------

def test_skips_unsupported_extension() -> None:
    findings = _scan("null\n", path="README.md")
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.cross_language_idiom = CrossLanguageIdiomConfig(enabled=False)
    rule = CrossLanguageIdiomRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="app.py",
        content="value = null\n",
        config=config,
    )
    assert len(findings) == 0


def test_severity_is_error() -> None:
    from slopcheck.models import Severity

    findings = _scan("value = null\n", path="app.py")
    assert findings[0].severity == Severity.ERROR


def test_skips_comment_lines_in_python() -> None:
    # A comment line containing `null` should not be flagged.
    findings = _scan("# null is not a valid Python keyword\n", path="app.py")
    assert len(findings) == 0


def test_skips_comment_lines_in_go() -> None:
    findings = _scan("// None is the Python keyword, not nil\n", path="main.go")
    assert len(findings) == 0

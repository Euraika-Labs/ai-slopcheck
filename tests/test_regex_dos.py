from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, RegexDosConfig
from slopcheck.rules.generic.regex_dos import RegexDosRule


def _scan(content: str, path: str = "src/validate.py") -> list:
    rule = RegexDosRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_nested_plus_quantifier() -> None:
    code = 're.compile("(a+)+")\n'
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].rule_id == "regex_dos"


def test_detects_nested_star_quantifier() -> None:
    code = 're.compile("(a*)+")\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_non_capturing_nested() -> None:
    code = 'pattern = "(?:ab+)+";\n'
    findings = _scan(code, path="src/validate.ts")
    assert len(findings) == 1


def test_allows_simple_pattern() -> None:
    code = 're.compile(r"^[a-z]+$")\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_simple_repetition() -> None:
    code = 're.compile(r"a{3,5}")\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_in_js_file() -> None:
    code = 'const re = new RegExp("(x+)+");\n'
    findings = _scan(code, path="src/parser.js")
    assert len(findings) == 1


def test_skips_unsupported_extension() -> None:
    rule = RegexDosRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/code.rb",
        content='r = Regexp.new("(a+)+")\n',
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.regex_dos = RegexDosConfig(enabled=False)
    rule = RegexDosRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/validate.py",
        content='re.compile("(a+)+")\n',
        config=config,
    )
    assert len(findings) == 0

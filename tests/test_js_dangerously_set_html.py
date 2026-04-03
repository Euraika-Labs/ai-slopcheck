from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, JsDangerouslySetHtmlConfig
from ai_slopcheck.rules.generic.js_dangerously_set_html import JsDangerouslySetHtmlRule

_PROP = "dangerouslySetInnerHTML"


def _scan(content: str, path: str = "src/RichText.tsx") -> list:
    rule = JsDangerouslySetHtmlRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_dangerous_prop_tsx() -> None:
    code = f"<div {_PROP}={{{{__html: content}}}} />\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert _PROP in findings[0].evidence


def test_detects_dangerous_prop_jsx() -> None:
    code = f"<span {_PROP}={{{{__html: body}}}}></span>\n"
    findings = _scan(code, path="src/Html.jsx")
    assert len(findings) == 1


def test_severity_is_error() -> None:
    code = f"<div {_PROP}={{{{__html: x}}}} />\n"
    findings = _scan(code)
    assert findings[0].severity.value == "error"


def test_no_findings_on_clean_jsx() -> None:
    code = "<div className='content'>{children}</div>\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_jsx_tsx_files() -> None:
    rule = JsDangerouslySetHtmlRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/util.ts",
        content=f"const x = '{_PROP}';\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.js_dangerously_set_html = JsDangerouslySetHtmlConfig(enabled=False)
    rule = JsDangerouslySetHtmlRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/RichText.tsx",
        content=f"<div {_PROP}={{{{__html: x}}}} />\n",
        config=config,
    )
    assert len(findings) == 0

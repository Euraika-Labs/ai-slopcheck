from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.bare_except_pass import BareExceptPassRule


def _scan(content: str) -> list:
    rule = BareExceptPassRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.py",
        content=content,
        config=AppConfig(),
    )


def test_detects_bare_except_pass():
    code = "try:\n    risky()\nexcept:\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].confidence.value == "high"


def test_detects_except_exception_pass():
    code = "try:\n    risky()\nexcept Exception:\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].confidence.value == "medium"


def test_detects_except_exception_as_e_pass():
    code = "try:\n    risky()\nexcept Exception as e:\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_empty_except_body():
    code = "try:\n    risky()\nexcept:\n\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_specific_exception():
    code = "try:\n    x = d[key]\nexcept KeyError:\n    pass\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_except_with_logging():
    code = "try:\n    risky()\nexcept Exception as e:\n    logger.error(e)\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_except_with_raise():
    code = "try:\n    risky()\nexcept:\n    raise\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_multiple_silent_handlers():
    code = (
        "try:\n    a()\nexcept:\n    pass\n\n"
        "try:\n    b()\nexcept Exception:\n    pass\n"
    )
    findings = _scan(code)
    assert len(findings) == 2


def test_skips_non_python():
    rule = BareExceptPassRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.js",
        content="try { } catch(e) { }",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule():
    from ai_slopcheck.config import BareExceptPassConfig

    config = AppConfig()
    config.rules.bare_except_pass = BareExceptPassConfig(enabled=False)
    findings = BareExceptPassRule().scan_file(
        repo_root=Path("/repo"),
        relative_path="src/x.py",
        content="try:\n    x()\nexcept:\n    pass\n",
        config=config,
    )
    assert len(findings) == 0

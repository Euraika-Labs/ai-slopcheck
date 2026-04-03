from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, GoErrorWrapConfig
from ai_slopcheck.rules.generic.go_error_wrap_missing_w import GoErrorWrapMissingWRule


def _scan(content: str, path: str = "service.go") -> list:
    rule = GoErrorWrapMissingWRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_errorf_with_percent_v_and_err() -> None:
    code = '    return fmt.Errorf("failed to open: %v", err)\n'
    findings = _scan(code)
    assert len(findings) == 1
    assert "%v" in findings[0].evidence


def test_detects_errorf_with_message_prefix_and_err() -> None:
    code = '    return fmt.Errorf("query failed: %v", err)\n'
    findings = _scan(code)
    assert len(findings) == 1


def test_does_not_flag_percent_w() -> None:
    code = '    return fmt.Errorf("failed to open: %w", err)\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_does_not_flag_percent_v_with_non_error_variable() -> None:
    # `value` is not `err` — should not flag.
    code = '    return fmt.Errorf("got %v items", value)\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_does_not_flag_errorf_without_percent_v() -> None:
    code = '    return fmt.Errorf("something went wrong")\n'
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_go_extension() -> None:
    findings = _scan('return fmt.Errorf("oops: %v", err)\n', path="main.py")
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.go_error_wrap_missing_w = GoErrorWrapConfig(enabled=False)
    rule = GoErrorWrapMissingWRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.go",
        content='    return fmt.Errorf("oops: %v", err)\n',
        config=config,
    )
    assert len(findings) == 0


def test_multiple_findings_in_file() -> None:
    code = (
        '    return fmt.Errorf("read failed: %v", err)\n'
        '    return fmt.Errorf("write failed: %v", err)\n'
    )
    findings = _scan(code)
    assert len(findings) == 2


def test_finding_has_suggestion_mentioning_percent_w() -> None:
    code = '    return fmt.Errorf("parse error: %v", err)\n'
    findings = _scan(code)
    assert findings[0].suggestion is not None
    assert "%w" in findings[0].suggestion


def test_severity_is_warning() -> None:
    from ai_slopcheck.models import Severity

    code = '    return fmt.Errorf("connect: %v", err)\n'
    findings = _scan(code)
    assert findings[0].severity == Severity.WARNING

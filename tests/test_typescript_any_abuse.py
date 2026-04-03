from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, TypescriptAnyAbuseConfig
from slopcheck.rules.generic.typescript_any_abuse import TypescriptAnyAbuseRule


def _scan(content: str, path: str = "src/service.ts") -> list:
    rule = TypescriptAnyAbuseRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_as_any() -> None:
    findings = _scan("const x = value as any;\n")
    assert len(findings) == 1
    assert "as any" in findings[0].message


def test_detects_ts_ignore() -> None:
    findings = _scan("// @ts-ignore\nconst x = badValue;\n")
    assert len(findings) == 1
    assert "@ts-ignore" in findings[0].message


def test_detects_ts_expect_error_no_explanation() -> None:
    findings = _scan("// @ts-expect-error\nconst x = badValue;\n")
    assert len(findings) == 1
    assert "@ts-expect-error" in findings[0].message


def test_allows_ts_expect_error_with_explanation() -> None:
    findings = _scan("// @ts-expect-error: legacy SDK returns untyped data\nconst x = val;\n")
    assert len(findings) == 0


def test_skips_dot_js_files() -> None:
    rule = TypescriptAnyAbuseRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.js",
        content="const x = value as any;\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_tsx_file_detected() -> None:
    findings = _scan("const el = (value as any).render();\n", path="src/Component.tsx")
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.typescript_any_abuse = TypescriptAnyAbuseConfig(enabled=False)
    rule = TypescriptAnyAbuseRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.ts",
        content="const x = value as any;\n",
        config=config,
    )
    assert len(findings) == 0


def test_one_finding_per_line() -> None:
    # Line with both as any and @ts-ignore — only one finding
    findings = _scan("// @ts-ignore\nconst x = (v as any);\n")
    # Two separate lines, each gets one finding
    assert len(findings) == 2

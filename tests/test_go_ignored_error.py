from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, GoIgnoredErrorConfig
from slopcheck.rules.generic.go_ignored_error import GoIgnoredErrorRule


def _scan(content: str, path: str = "main.go") -> list:
    rule = GoIgnoredErrorRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_single_blank_identifier() -> None:
    # os.Remove is now in the allowed list (golangci-lint convention)
    # Use a non-allowed function
    findings = _scan("    _ = db.Execute(ctx, query)\n")
    assert len(findings) == 1
    assert "db.Execute" in findings[0].message


def test_detects_double_blank_identifier() -> None:
    findings = _scan("    _, _ = db.Query(ctx, q)\n")
    assert len(findings) == 1
    assert "db.Query" in findings[0].message


def test_allows_fmt_fprintf() -> None:
    # fmt.Fprintf is the idiomatic exception
    findings = _scan("    _ = fmt.Fprintf(w, msg)\n")
    assert len(findings) == 0


def test_allows_fmt_fprintln() -> None:
    findings = _scan("    _ = fmt.Fprintln(w, msg)\n")
    assert len(findings) == 0


def test_proper_error_handling() -> None:
    code = "    err := os.Remove(path)\n    if err != nil {\n        log.Fatal(err)\n    }\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_go_extension() -> None:
    rule = GoIgnoredErrorRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.py",
        content="    _ = os.Remove(path)\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.go_ignored_error = GoIgnoredErrorConfig(enabled=False)
    rule = GoIgnoredErrorRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.go",
        content="    _ = os.Remove(path)\n",
        config=config,
    )
    assert len(findings) == 0


def test_allows_os_remove() -> None:
    # os.Remove is excluded (golangci-lint convention)
    findings = _scan("    _ = os.Remove(path)\n")
    assert len(findings) == 0


def test_allows_close_method() -> None:
    # *.Close is excluded (golangci-lint convention)
    findings = _scan("    _ = conn.Close()\n")
    assert len(findings) == 0


def test_multiple_ignored_errors() -> None:
    code = "    _ = db.Execute(a)\n    _ = db.Execute(b)\n"
    findings = _scan(code)
    assert len(findings) == 2

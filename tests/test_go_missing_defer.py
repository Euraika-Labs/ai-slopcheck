from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, GoMissingDeferConfig
from slopcheck.rules.generic.go_missing_defer import GoMissingDeferRule


def _scan(content: str, path: str = "main.go") -> list:
    rule = GoMissingDeferRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_http_get_no_defer() -> None:
    code = (
        "resp, err := http.Get(url)\n"
        "if err != nil { log.Fatal(err) }\n"
        "body, _ := io.ReadAll(resp.Body)\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert "resp" in findings[0].message


def test_detects_os_open_no_defer() -> None:
    code = (
        "f, err := os.Open(path)\n"
        "if err != nil { return err }\n"
        "data, _ := io.ReadAll(f)\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert "f" in findings[0].message


def test_detects_os_create_no_defer() -> None:
    code = (
        "out, err := os.Create(dst)\n"
        "if err != nil { return err }\n"
        "_, _ = out.Write(data)\n"
    )
    findings = _scan(code)
    assert len(findings) == 1


def test_safe_http_get_with_defer_body_close() -> None:
    code = (
        "resp, err := http.Get(url)\n"
        "if err != nil { log.Fatal(err) }\n"
        "defer resp.Body.Close()\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_safe_os_open_with_defer_close() -> None:
    code = (
        "f, err := os.Open(path)\n"
        "if err != nil { return err }\n"
        "defer f.Close()\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_go_extension() -> None:
    rule = GoMissingDeferRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.py",
        content="resp, err := http.Get(url)\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.go_missing_defer = GoMissingDeferConfig(enabled=False)
    rule = GoMissingDeferRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="main.go",
        content=(
            "resp, err := http.Get(url)\n"
            "if err != nil { log.Fatal(err) }\n"
        ),
        config=config,
    )
    assert len(findings) == 0


def test_multiple_opens_without_defers() -> None:
    code = (
        "f, err := os.Open(a)\n"
        "if err != nil { return err }\n"
        "\n"
        "g, err := os.Open(b)\n"
        "if err != nil { return err }\n"
    )
    findings = _scan(code)
    assert len(findings) == 2

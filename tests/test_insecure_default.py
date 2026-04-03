from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, InsecureDefaultConfig
from slopcheck.rules.generic.insecure_default import InsecureDefaultRule


def _scan(content: str, path: str = "src/service.py") -> list:
    rule = InsecureDefaultRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_verify_false() -> None:
    findings = _scan("requests.get(url, verify=False)\n")
    assert len(findings) == 1
    assert "verify=False" in findings[0].message


def test_detects_ssl_unverified_context() -> None:
    findings = _scan("ctx = ssl._create_unverified_context()\n")
    assert len(findings) == 1
    assert "ssl._create_unverified_context" in findings[0].message


def test_detects_debug_true() -> None:
    findings = _scan("DEBUG = True\n")
    assert len(findings) == 1
    assert "DEBUG=True" in findings[0].message


def test_detects_cors_wildcard() -> None:
    findings = _scan('allow_origins=["*"]\n')
    assert len(findings) == 1
    assert "CORS" in findings[0].message


def test_detects_cors_wildcard_star_string() -> None:
    findings = _scan('origins = "*"\n')
    assert len(findings) == 1


def test_safe_verify_true() -> None:
    findings = _scan("requests.get(url, verify=True)\n")
    assert len(findings) == 0


def test_safe_debug_false() -> None:
    findings = _scan("DEBUG = False\n")
    assert len(findings) == 0


def test_safe_cors_specific_origin() -> None:
    findings = _scan('allow_origins=["https://example.com"]\n')
    assert len(findings) == 0


def test_skips_non_matching_extension() -> None:
    rule = InsecureDefaultRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="README.md",
        content="verify=False\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.insecure_default = InsecureDefaultConfig(enabled=False)
    rule = InsecureDefaultRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.py",
        content="requests.get(url, verify=False)\n",
        config=config,
    )
    assert len(findings) == 0


def test_multiple_patterns_one_finding_per_line() -> None:
    # A line with both verify=False and DEBUG=True should produce only 1 finding
    findings = _scan("x = requests.get(url, verify=False)  # DEBUG = True\n")
    assert len(findings) == 1

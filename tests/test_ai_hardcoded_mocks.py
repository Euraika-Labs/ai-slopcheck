from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AiHardcodedMocksConfig, AppConfig
from ai_slopcheck.rules.generic.ai_hardcoded_mocks import AiHardcodedMocksRule


def _make_config() -> AppConfig:
    config = AppConfig()
    config.rules.ai_hardcoded_mocks = AiHardcodedMocksConfig(enabled=True)
    return config


def _scan(content: str, path: str = "src/service.py") -> list:
    rule = AiHardcodedMocksRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=_make_config(),
    )


def test_detects_john_doe():
    findings = _scan('name = "John Doe"\n')
    assert len(findings) == 1
    assert "mock person name" in findings[0].message


def test_detects_jane_doe():
    findings = _scan("name = 'Jane Doe'\n")
    assert len(findings) == 1


def test_detects_acme_corp():
    findings = _scan('company = "Acme Corporation"\n')
    assert len(findings) == 1
    assert "mock company name" in findings[0].message


def test_allows_example_com_email():
    # example.com is RFC 2606 — allowed by default
    findings = _scan('email = "test@example.com"\n')
    assert len(findings) == 0


def test_detects_mock_email_non_rfc():
    findings = _scan('email = "test@testcompany.com"\n')
    assert len(findings) == 1
    assert "mock email" in findings[0].message


def test_detects_555_phone():
    findings = _scan('phone = "555-123-4567"\n')
    assert len(findings) == 1


def test_ignores_test_files():
    findings = _scan(
        'name = "John Doe"\n',
        path="tests/test_user.py",
    )
    assert len(findings) == 0


def test_ignores_fixture_files():
    findings = _scan(
        'name = "John Doe"\n',
        path="tests/fixtures/users.py",
    )
    assert len(findings) == 0


def test_ignores_real_names():
    findings = _scan('author = "Guido van Rossum"\n')
    assert len(findings) == 0


def test_ignores_real_emails():
    findings = _scan('support = "support@company.com"\n')
    assert len(findings) == 0


def test_one_finding_per_line():
    # Even if multiple patterns match, we only report one per line
    findings = _scan('data = {"name": "John Doe", "email": "test@example.com"}\n')
    assert len(findings) == 1

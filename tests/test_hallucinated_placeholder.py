from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.hallucinated_placeholder import HallucinatedPlaceholderRule


def _scan(content: str, path: str = "src/config.py") -> list:
    rule = HallucinatedPlaceholderRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_your_api_key():
    findings = _scan('API_KEY = "your-api-key-here"\n')
    assert len(findings) == 1


def test_detects_replace_me():
    findings = _scan('secret = "REPLACE_ME"\n')
    assert len(findings) == 1


def test_allows_example_com_by_default():
    # example.com is in allowed_domains by default (RFC 2606)
    findings = _scan('url = "https://api.example.com/v1/data"\n')
    assert len(findings) == 0


def test_detects_example_url_when_not_allowed():
    from ai_slopcheck.config import HallucinatedPlaceholderConfig

    config = AppConfig()
    config.rules.hallucinated_placeholder = HallucinatedPlaceholderConfig(
        allowed_domains=[]
    )
    rule = HallucinatedPlaceholderRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/config.py",
        content='url = "https://api.example.com/v1/data"\n',
        config=config,
    )
    assert len(findings) == 1


def test_detects_fake_path():
    findings = _scan('config_path = "path/to/your/config.yaml"\n')
    assert len(findings) == 1


def test_detects_insert_marker():
    findings = _scan('token = "<INSERT_YOUR_TOKEN>"\n')
    assert len(findings) == 1


def test_ignores_real_url():
    findings = _scan('url = "https://api.github.com/repos"\n')
    assert len(findings) == 0


def test_ignores_test_files():
    findings = _scan(
        'API_KEY = "your-api-key-here"\n',
        path="tests/test_config.py",
    )
    assert len(findings) == 0


def test_ignores_fixture_files():
    findings = _scan(
        'url = "https://example.com"\n',
        path="tests/fixtures/sample.py",
    )
    assert len(findings) == 0


def test_ignores_comment_lines():
    findings = _scan('# url = "https://api.example.com/docs"\n')
    assert len(findings) == 0


def test_detects_sk_xxxx():
    findings = _scan('openai_key = "sk-xxxx"\n')
    assert len(findings) == 1


def test_ignores_example_file_path():
    # Files under examples/ are skipped (same as fixture/test files)
    findings = _scan(
        'API_KEY = "your-api-key-here"\n',
        path="examples/config.py",
    )
    assert len(findings) == 0

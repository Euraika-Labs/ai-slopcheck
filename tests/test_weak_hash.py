from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, WeakHashConfig
from slopcheck.rules.generic.weak_hash import WeakHashRule


def _scan(content: str, path: str = "src/crypto.py") -> list:
    rule = WeakHashRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_hashlib_md5() -> None:
    code = "h = hashlib.md5(data)\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert findings[0].rule_id == "weak_hash"


def test_detects_hashlib_sha1() -> None:
    code = "digest = hashlib.sha1(content).hexdigest()\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_allows_hashlib_sha256() -> None:
    code = "h = hashlib.sha256(data).digest()\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_hashlib_sha512() -> None:
    code = "h = hashlib.sha512(data).hexdigest()\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_in_js_file() -> None:
    code = "const h = crypto.createHash('md5').update(data).digest('hex');\n"
    findings = _scan(code, path="src/hash.ts")
    assert len(findings) == 1


def test_detects_bare_md5_call() -> None:
    code = "checksum = md5(payload)\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_skips_unsupported_extension() -> None:
    rule = WeakHashRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/code.rb",
        content="digest = md5(data)\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.weak_hash = WeakHashConfig(enabled=False)
    rule = WeakHashRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/crypto.py",
        content="h = hashlib.md5(data)\n",
        config=config,
    )
    assert len(findings) == 0

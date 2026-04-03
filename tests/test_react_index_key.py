from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, ReactIndexKeyConfig
from ai_slopcheck.rules.generic.react_index_key import ReactIndexKeyRule


def _scan(content: str, path: str = "src/List.tsx") -> list:
    rule = ReactIndexKeyRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_key_index() -> None:
    code = "{items.map((item, index) => <li key={index}>{item}</li>)}\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "key={index}" in findings[0].evidence


def test_detects_key_idx() -> None:
    code = "{items.map((item, idx) => <li key={idx}>{item}</li>)}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_key_i() -> None:
    code = "{items.map((item, i) => <div key={i}>{item}</div>)}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_safe_key_item_id() -> None:
    code = "{items.map((item) => <li key={item.id}>{item.name}</li>)}\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_jsx_tsx() -> None:
    rule = ReactIndexKeyRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.ts",
        content="{items.map((item, index) => <li key={index}>{item}</li>)}\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_jsx_file_detected() -> None:
    findings = _scan(
        "{items.map((item, index) => <li key={index}>{item}</li>)}\n",
        path="src/List.jsx",
    )
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.react_index_key = ReactIndexKeyConfig(enabled=False)
    rule = ReactIndexKeyRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/List.tsx",
        content="{items.map((item, index) => <li key={index}>{item}</li>)}\n",
        config=config,
    )
    assert len(findings) == 0

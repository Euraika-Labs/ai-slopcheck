from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, ReactAsyncUseeffectConfig
from ai_slopcheck.rules.generic.react_async_useeffect import ReactAsyncUseeffectRule


def _scan(content: str, path: str = "src/Component.tsx") -> list:
    rule = ReactAsyncUseeffectRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_useeffect_async() -> None:
    code = "useEffect(async () => {\n  await fetchData();\n}, []);\n"
    findings = _scan(code)
    assert len(findings) == 1
    assert "useEffect" in findings[0].message


def test_detects_useeffect_async_multiword() -> None:
    code = "  useEffect(  async () => {\n    await load();\n  }, [id]);\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_safe_inner_async_function() -> None:
    code = (
        "useEffect(() => {\n"
        "  const run = async () => { await fetchData(); };\n"
        "  run();\n"
        "}, []);\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_matching_extension() -> None:
    rule = ReactAsyncUseeffectRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/Component.vue",
        content="useEffect(async () => { await x(); }, []);\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_js_file_detected() -> None:
    findings = _scan(
        "useEffect(async () => { await fetchData(); }, []);\n",
        path="src/Component.js",
    )
    assert len(findings) == 1


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.react_async_useeffect = ReactAsyncUseeffectConfig(enabled=False)
    rule = ReactAsyncUseeffectRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/Component.tsx",
        content="useEffect(async () => { await fetchData(); }, []);\n",
        config=config,
    )
    assert len(findings) == 0

from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig, JsAwaitInLoopConfig
from ai_slopcheck.rules.generic.js_await_in_loop import JsAwaitInLoopRule


def _scan(content: str, path: str = "src/service.ts") -> list:
    rule = JsAwaitInLoopRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_await_in_for_loop() -> None:
    code = """\
async function fetchAll(ids) {
    for (const id of ids) {
        const result = await fetch(id);
    }
}
"""
    findings = _scan(code)
    assert len(findings) >= 1
    assert any("await" in f.evidence for f in findings)


def test_detects_await_in_while_loop() -> None:
    code = """\
async function poll() {
    while (running) {
        const data = await getData();
    }
}
"""
    findings = _scan(code)
    assert len(findings) >= 1


def test_detects_await_in_for_loop_js() -> None:
    code = """\
async function run(items) {
    for (let i = 0; i < items.length; i++) {
        await process(items[i]);
    }
}
"""
    findings = _scan(code, path="src/util.js")
    assert len(findings) >= 1


def test_allows_await_outside_loop() -> None:
    code = """\
async function fetchOne(id) {
    const result = await fetch(id);
    return result;
}
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_allows_promise_all_pattern() -> None:
    code = """\
async function fetchAll(ids) {
    const results = await Promise.all(ids.map(id => fetch(id)));
    return results;
}
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_skips_non_js_ts_files() -> None:
    rule = JsAwaitInLoopRule()
    code = "for x in items:\n    await thing(x)\n"
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/code.py",
        content=code,
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_skips_test_files() -> None:
    code = """\
for (const id of ids) {
    const r = await fetch(id);
}
"""
    findings = _scan(code, path="tests/service.test.ts")
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.js_await_in_loop = JsAwaitInLoopConfig(enabled=False)
    rule = JsAwaitInLoopRule()
    code = """\
for (const id of ids) {
    await fetch(id);
}
"""
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/service.ts",
        content=code,
        config=config,
    )
    assert len(findings) == 0

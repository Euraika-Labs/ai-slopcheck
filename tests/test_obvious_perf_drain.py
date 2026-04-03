from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig, ObviousPerfDrainConfig
from slopcheck.rules.generic.obvious_perf_drain import ObviousPerfDrainRule


def _make_config() -> AppConfig:
    config = AppConfig()
    config.rules.obvious_perf_drain = ObviousPerfDrainConfig(enabled=True)
    return config


def _scan(content: str, path: str = "src/algo.py") -> list:
    rule = ObviousPerfDrainRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=_make_config(),
    )


def test_detects_nested_for_loops_python() -> None:
    code = """\
def match(a, b):
    for x in a:
        for y in b:
            if x == y:
                return True
"""
    findings = _scan(code)
    assert len(findings) >= 1
    assert findings[0].rule_id == "obvious_perf_drain"


def test_allows_single_for_loop_python() -> None:
    code = """\
def sum_all(items):
    total = 0
    for item in items:
        total += item
    return total
"""
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_nested_for_loops_js() -> None:
    code = """\
function findPairs(a, b) {
    for (let i = 0; i < a.length; i++) {
        for (let j = 0; j < b.length; j++) {
            if (a[i] === b[j]) return true;
        }
    }
}
"""
    findings = _scan(code, path="src/algo.ts")
    assert len(findings) >= 1


def test_allows_single_for_loop_js() -> None:
    code = """\
function sumAll(items) {
    let total = 0;
    for (const item of items) {
        total += item;
    }
    return total;
}
"""
    findings = _scan(code, path="src/algo.ts")
    assert len(findings) == 0


def test_detects_nested_while_loops_python() -> None:
    code = """\
def wait():
    while a:
        while b:
            tick()
"""
    findings = _scan(code)
    assert len(findings) >= 1


def test_skips_unsupported_extension() -> None:
    rule = ObviousPerfDrainRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/code.rb",
        content="for x in a:\n    for y in b:\n        use(x, y)\n",
        config=_make_config(),
    )
    assert len(findings) == 0


def test_disabled_rule() -> None:
    config = AppConfig()
    config.rules.obvious_perf_drain = ObviousPerfDrainConfig(enabled=False)
    rule = ObviousPerfDrainRule()
    code = """\
for x in a:
    for y in b:
        use(x, y)
"""
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/algo.py",
        content=code,
        config=config,
    )
    assert len(findings) == 0

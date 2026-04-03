"""Tests for slopcheck/rules/generic/api_contract_breaking.py."""
from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import ApiContractBreakingConfig, AppConfig, RulesConfig
from ai_slopcheck.rules.generic.api_contract_breaking import ApiContractBreakingRule


def _make_config(*, enabled: bool = True) -> AppConfig:
    return AppConfig(
        rules=RulesConfig(
            api_contract_breaking=ApiContractBreakingConfig(enabled=enabled),
        )
    )


# ---------------------------------------------------------------------------
# Commented-out route decorators (Python)
# ---------------------------------------------------------------------------


def test_commented_out_app_get_python() -> None:
    rule = ApiContractBreakingRule()
    content = "# @app.get('/users')\ndef list_users(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "api_contract_breaking"
    assert "commented" in f.message.lower()
    assert f.location.line == 1
    assert "commented-route" in f.tags


def test_commented_out_router_post_python() -> None:
    rule = ApiContractBreakingRule()
    content = "# @router.post('/items')\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="routes.py",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1


def test_active_python_route_no_finding() -> None:
    rule = ApiContractBreakingRule()
    content = "@app.get('/users')\ndef list_users(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Commented-out route decorators (JS/TS)
# ---------------------------------------------------------------------------


def test_commented_out_express_get_js() -> None:
    rule = ApiContractBreakingRule()
    content = "// app.get('/users', listUsers);\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="server.js",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1
    f = findings[0]
    assert "commented" in f.message.lower()
    assert f.location.line == 1


def test_commented_out_router_post_ts() -> None:
    rule = ApiContractBreakingRule()
    content = "// router.post('/items', createItem);\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="routes.ts",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1


def test_active_express_route_no_finding() -> None:
    rule = ApiContractBreakingRule()
    content = "app.get('/users', listUsers);\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="server.js",
        content=content,
        config=_make_config(),
    )
    assert findings == []


# ---------------------------------------------------------------------------
# @deprecated decorator on a route handler (Python)
# ---------------------------------------------------------------------------


def test_deprecated_before_fastapi_route() -> None:
    rule = ApiContractBreakingRule()
    content = "@deprecated\n@app.get('/old-endpoint')\ndef old_handler(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1
    f = findings[0]
    assert "deprecated" in f.message.lower()
    assert "deprecated-route" in f.tags
    assert f.location.line == 2


def test_no_finding_when_deprecated_not_before_route() -> None:
    rule = ApiContractBreakingRule()
    content = "@deprecated\ndef some_helper(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="utils.py",
        content=content,
        config=_make_config(),
    )
    # @deprecated is on a non-route line; no api_contract_breaking finding expected
    assert findings == []


# ---------------------------------------------------------------------------
# TODO / FIXME comment on route decorator line
# ---------------------------------------------------------------------------


def test_todo_on_route_line_python() -> None:
    rule = ApiContractBreakingRule()
    content = "@app.get('/items')  # TODO remove this endpoint\ndef get_items(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1
    f = findings[0]
    assert "TODO" in f.message
    assert "todo-route" in f.tags
    assert f.location.line == 1


def test_fixme_on_route_line_python() -> None:
    rule = ApiContractBreakingRule()
    content = "@app.delete('/v1/resource')  # FIXME deprecate properly\ndef remove(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1
    assert "FIXME" in findings[0].message


def test_todo_on_express_route_js() -> None:
    rule = ApiContractBreakingRule()
    content = "app.get('/old', handler); // TODO remove\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="server.js",
        content=content,
        config=_make_config(),
    )
    assert len(findings) == 1


def test_clean_route_no_todo() -> None:
    rule = ApiContractBreakingRule()
    content = "@app.get('/clean')\ndef clean_handler(): pass\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Rule disabled
# ---------------------------------------------------------------------------


def test_rule_disabled_returns_no_findings() -> None:
    rule = ApiContractBreakingRule()
    content = "# @app.get('/users')\n@deprecated\n@app.post('/x')  # TODO\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(enabled=False),
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Unsupported extension
# ---------------------------------------------------------------------------


def test_unsupported_extension_returns_empty() -> None:
    rule = ApiContractBreakingRule()
    content = "# @app.get('/users')\n"
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="notes.txt",
        content=content,
        config=_make_config(),
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Fingerprint stability
# ---------------------------------------------------------------------------


def test_fingerprint_is_stable() -> None:
    rule = ApiContractBreakingRule()
    content = "# @app.get('/users')\n"

    f1 = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    f2 = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    assert f1[0].fingerprint == f2[0].fingerprint


def test_fingerprint_differs_by_path() -> None:
    rule = ApiContractBreakingRule()
    content = "# @app.get('/users')\n"

    f1 = rule.scan_file(
        repo_root=Path("."),
        relative_path="api.py",
        content=content,
        config=_make_config(),
    )
    f2 = rule.scan_file(
        repo_root=Path("."),
        relative_path="other.py",
        content=content,
        config=_make_config(),
    )
    assert f1[0].fingerprint != f2[0].fingerprint

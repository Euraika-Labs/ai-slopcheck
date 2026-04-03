from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.bare_except_pass_js import BareExceptPassJsRule


def _scan(content: str, path: str = "src/handler.ts") -> list:
    rule = BareExceptPassJsRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_empty_catch_oneline():
    code = "try { riskyCall(); } catch (e) { }\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_empty_catch_multiline():
    code = "try {\n  riskyCall();\n} catch (e) {\n}\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_catch_no_param():
    code = "try { foo(); } catch { }\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_catch_with_handling():
    code = (
        "try {\n"
        "  riskyCall();\n"
        "} catch (e) {\n"
        "  console.error(e);\n"
        "}\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_non_js():
    code = "try { } catch (e) { }\n"
    findings = _scan(code, path="main.py")
    assert len(findings) == 0

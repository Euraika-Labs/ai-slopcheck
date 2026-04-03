from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.dead_code_comment import DeadCodeCommentRule


def _scan(content: str, path: str = "src/main.py") -> list:
    rule = DeadCodeCommentRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_four_consecutive_code_comments():
    code = (
        "# result = old_function(x)\n"
        "# for item in result:\n"
        "#     process(item)\n"
        "# return result\n"
    )
    findings = _scan(code)
    assert len(findings) == 1
    assert "4" in findings[0].message


def test_ignores_three_code_comments():
    # Default threshold is 4, so 3 should NOT fire
    code = (
        "# result = old_function(x)\n"
        "# for item in result:\n"
        "#     process(item)\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_prose_comments():
    code = (
        "# This is a description of the function.\n"
        "# It handles user authentication.\n"
        "# Returns True if the user is valid.\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_commented_imports():
    code = (
        "# import os\n"
        "# import sys\n"
        "# from pathlib import Path\n"
        "# import json\n"
    )
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_commented_assignments():
    code = (
        "# x = compute_value()\n"
        "# y = transform(x)\n"
        "# result = combine(x, y)\n"
        "# final = process(result)\n"
    )
    findings = _scan(code)
    assert len(findings) == 1


def test_works_with_js_comments():
    code = (
        "// const result = fetchData();\n"
        "// for (const item of result) {\n"
        "//     process(item);\n"
        "//     render(item);\n"
    )
    findings = _scan(code, path="src/main.js")
    assert len(findings) == 1


def test_multiple_blocks():
    code = (
        "# x = foo()\n# y = bar()\n# z = baz()\n# w = qux()\n"
        "real_code = 1\n"
        "# a = one()\n# b = two()\n# c = three()\n# d = four()\n"
    )
    findings = _scan(code)
    assert len(findings) == 2


def test_skips_unsupported_extensions():
    rule = DeadCodeCommentRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="data.json",
        content="// x = 1\n// y = 2\n// z = 3\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_configurable_min_lines():
    from slopcheck.config import DeadCodeCommentConfig

    config = AppConfig()
    config.rules.dead_code_comment = DeadCodeCommentConfig(min_consecutive_lines=5)
    code = "# x = 1\n# y = 2\n# z = 3\n"
    rule = DeadCodeCommentRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.py",
        content=code,
        config=config,
    )
    assert len(findings) == 0


def test_ignores_prose_with_keywords():
    # Three lines of natural-language prose with keywords should NOT fire
    code = (
        "# if the user is authenticated, return the token\n"
        "# this is needed for the session to stay valid\n"
        "# see the auth module for details on expiry logic\n"
    )
    findings = _scan(code)
    assert len(findings) == 0


def test_code_at_end_of_file():
    # Commented code at EOF (no trailing newline after the block) still fires
    code = (
        "real_code = 1\n"
        "# x = old_func()\n"
        "# y = transform(x)\n"
        "# result = combine(x, y)\n"
        "# final = process(result)"
    )
    findings = _scan(code)
    assert len(findings) == 1

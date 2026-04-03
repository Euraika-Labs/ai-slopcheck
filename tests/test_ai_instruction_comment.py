from __future__ import annotations

from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.rules.generic.ai_instruction_comment import AiInstructionCommentRule


def _scan(content: str, path: str = "src/main.py") -> list:
    rule = AiInstructionCommentRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_implement_this_logic():
    code = "# TODO: implement the remaining logic here\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_common_add_comment():
    # "Add" is too common in normal developer comments — no longer flagged
    code = "// Add your actual implementation here\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_detects_fill_the_implementation():
    code = "# fill the actual implementation\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_complete_the_function():
    code = "// complete this function body\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_omitted_for_brevity():
    code = "# ... omitted for brevity\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_detects_rest_of_code():
    code = "// rest of the code unchanged\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_ignores_normal_todo():
    code = "# TODO: fix edge case for negative numbers\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_normal_comment():
    code = "# This function handles user authentication\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_ignores_code_line():
    code = "result = implement_feature(data)\n"
    findings = _scan(code)
    assert len(findings) == 0


def test_works_with_c_style_comments():
    code = "/* implement the actual logic */\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_case_insensitive():
    code = "# IMPLEMENT THE REMAINING CODE HERE\n"
    findings = _scan(code)
    assert len(findings) == 1


def test_disabled_rule():
    from ai_slopcheck.config import AiInstructionCommentConfig

    config = AppConfig()
    config.rules.ai_instruction_comment = AiInstructionCommentConfig(enabled=False)
    rule = AiInstructionCommentRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.py",
        content="# implement the remaining logic\n",
        config=config,
    )
    assert len(findings) == 0

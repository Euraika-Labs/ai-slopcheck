from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.ai_conversational_bleed import AiConversationalBleedRule


def _scan(content: str, path: str = "src/main.py") -> list:
    rule = AiConversationalBleedRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path=path,
        content=content,
        config=AppConfig(),
    )


def test_detects_here_is_the_code():
    findings = _scan("Here is the updated code:\n")
    assert len(findings) == 1
    assert findings[0].severity.value == "error"


def test_detects_certainly():
    findings = _scan("Certainly! Let me help you with that.\n")
    assert len(findings) == 1


def test_detects_sure_here():
    findings = _scan("Sure, here is the implementation:\n")
    assert len(findings) == 1


def test_detects_code_fence():
    findings = _scan("```python\n")
    assert len(findings) == 1
    assert "markdown" in findings[0].tags


def test_detects_js_code_fence():
    findings = _scan("```javascript\n")
    assert len(findings) == 1


def test_ignores_normal_code():
    findings = _scan("result = compute_value(data)\n")
    assert len(findings) == 0


def test_ignores_normal_string():
    findings = _scan('message = "Here is some data"\n')
    assert len(findings) == 0


def test_detects_ive_created():
    findings = _scan("I've created the following function:\n")
    assert len(findings) == 1


def test_detects_let_me_help():
    findings = _scan("Let me help you fix this:\n")
    assert len(findings) == 1


def test_disabled_rule():
    from slopcheck.config import AiConversationalBleedConfig

    config = AppConfig()
    config.rules.ai_conversational_bleed = AiConversationalBleedConfig(enabled=False)
    rule = AiConversationalBleedRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.py",
        content="Certainly! Here is the code:\n",
        config=config,
    )
    assert len(findings) == 0


def test_ignores_prompt_template_files():
    # Files inside a prompts/ directory are allowed to contain conversational text
    findings = _scan("Certainly! Here is the code:\n", path="prompts/system.py")
    assert len(findings) == 0


def test_ignores_test_files():
    # Test files may contain expected AI bleed strings as fixtures
    findings = _scan("Here is the updated code:\n", path="tests/test_ai.py")
    assert len(findings) == 0

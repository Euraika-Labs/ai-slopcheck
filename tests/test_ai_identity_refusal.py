from __future__ import annotations

from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.rules.generic.ai_identity_refusal import AiIdentityRefusalRule


def _scan(content: str) -> list:
    rule = AiIdentityRefusalRule()
    return rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="src/main.py",
        content=content,
        config=AppConfig(),
    )


def test_detects_as_an_ai():
    findings = _scan("As an AI language model, I cannot provide this.\n")
    assert len(findings) == 1
    assert findings[0].severity.value == "error"
    assert findings[0].confidence.value == "high"


def test_detects_i_am_an_ai():
    findings = _scan("I am an AI and cannot help with that.\n")
    assert len(findings) == 1


def test_detects_i_cannot_fulfill():
    findings = _scan("I cannot fulfill this request.\n")
    assert len(findings) == 1


def test_detects_i_apologize_but():
    findings = _scan("I apologize, but I cannot assist with that.\n")
    assert len(findings) == 1


def test_detects_im_not_able():
    findings = _scan("I'm not able to generate that code.\n")
    assert len(findings) == 1


def test_ignores_normal_code():
    findings = _scan("result = model.predict(data)\n")
    assert len(findings) == 0


def test_ignores_unrelated_apologize():
    findings = _scan('message = "We apologize for the inconvenience"\n')
    assert len(findings) == 0


def test_case_insensitive():
    findings = _scan("as an ai language model, I cannot do this\n")
    assert len(findings) == 1


def test_ignores_prompt_files():
    # Prompt files legitimately contain AI refusal text as examples
    rule = AiIdentityRefusalRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="prompts/few_shot.py",
        content="As an AI language model, I cannot provide this.\n",
        config=AppConfig(),
    )
    assert len(findings) == 0


def test_ignores_template_files():
    # Template files may include AI identity text as placeholders
    rule = AiIdentityRefusalRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="templates/ai_response.py",
        content="I'm not able to generate that code.\n",
        config=AppConfig(),
    )
    assert len(findings) == 0

from pathlib import Path

from slopcheck.config import AppConfig, PlaceholderTokensConfig, RulesConfig
from slopcheck.rules.generic.placeholder_tokens import PlaceholderTokensRule


def test_placeholder_tokens_rule_finds_todo() -> None:
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content='print("hello")\n# TODO remove\n',
        config=AppConfig(),
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "placeholder_tokens"
    assert findings[0].location.line == 2
    assert findings[0].severity.value == "warning"


def test_placeholder_tokens_finds_multiple_tokens_on_same_line() -> None:
    """finditer should find ALL matches per line, not just the first."""
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODO FIXME cleanup\n",
        config=AppConfig(),
    )

    assert len(findings) == 2
    tokens_found = {f.evidence for f in findings}
    assert tokens_found == {"TODO", "FIXME"}
    # Both findings should be on line 1.
    assert all(f.location.line == 1 for f in findings)


def test_placeholder_tokens_rule_disabled_returns_nothing() -> None:
    rule = PlaceholderTokensRule()
    config = AppConfig(
        rules=RulesConfig(
            placeholder_tokens=PlaceholderTokensConfig(enabled=False),
        )
    )
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODO this should be ignored\n",
        config=config,
    )

    assert findings == []


def test_placeholder_tokens_empty_banned_list_returns_nothing() -> None:
    rule = PlaceholderTokensRule()
    config = AppConfig(
        rules=RulesConfig(
            placeholder_tokens=PlaceholderTokensConfig(banned_tokens=[]),
        )
    )
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODO FIXME HACK\n",
        config=config,
    )

    assert findings == []


def test_placeholder_tokens_custom_banned_tokens() -> None:
    """Custom banned_tokens list should replace the defaults entirely."""
    rule = PlaceholderTokensRule()
    config = AppConfig(
        rules=RulesConfig(
            placeholder_tokens=PlaceholderTokensConfig(
                banned_tokens=["PLACEHOLDER", "STUB"],
            ),
        )
    )
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="x = PLACEHOLDER  # TODO should not match\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "PLACEHOLDER"


def test_placeholder_tokens_respects_word_boundary() -> None:
    """TODOLIST should NOT match the TODO token because of \\b boundaries."""
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODOLIST is not a match\n# TODO is a match\n",
        config=AppConfig(),
    )

    assert len(findings) == 1
    assert findings[0].evidence == "TODO"
    assert findings[0].location.line == 2


def test_placeholder_tokens_unsupported_extension_returns_nothing() -> None:
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="data.csv",
        content="TODO,FIXME,HACK\n",
        config=AppConfig(),
    )

    assert findings == []


def test_placeholder_tokens_empty_content_returns_nothing() -> None:
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="",
        config=AppConfig(),
    )

    assert findings == []


def test_placeholder_tokens_finding_fields() -> None:
    """Verify evidence, suggestion, tags, confidence, and fingerprint stability."""
    rule = PlaceholderTokensRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODO fix this\n",
        config=AppConfig(),
    )

    assert len(findings) == 1
    finding = findings[0]

    # Evidence is the matched token.
    assert finding.evidence == "TODO"

    # Suggestion is populated.
    assert finding.suggestion is not None
    assert "placeholder" in finding.suggestion.lower() or "replace" in finding.suggestion.lower()

    # Tags are set.
    assert "placeholder" in finding.tags
    assert "cleanup" in finding.tags

    # Confidence is HIGH.
    assert finding.confidence.value == "high"

    # Fingerprint is stable across calls.
    findings_again = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/example.py",
        content="# TODO fix this\n",
        config=AppConfig(),
    )
    assert findings_again[0].fingerprint == finding.fingerprint

    # Fingerprint uses \x00 separator (different path => different fingerprint).
    findings_other_path = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/other.py",
        content="# TODO fix this\n",
        config=AppConfig(),
    )
    assert findings_other_path[0].fingerprint != finding.fingerprint

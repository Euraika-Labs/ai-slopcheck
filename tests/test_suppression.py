from __future__ import annotations

from slopcheck.engine.suppression import is_suppressed, parse_suppressions


def test_same_line_ignore():
    content = 'x = 1  # slopcheck: ignore[placeholder_tokens]\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "placeholder_tokens")
    assert not is_suppressed(s, 1, "other_rule")


def test_next_line_ignore():
    content = '# slopcheck: ignore-next[bare_except_pass]\nexcept:\n    pass\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 2, "bare_except_pass")
    assert not is_suppressed(s, 1, "bare_except_pass")


def test_multiple_rules():
    content = 'x = 1  # slopcheck: ignore[rule_a, rule_b]\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "rule_a")
    assert is_suppressed(s, 1, "rule_b")
    assert not is_suppressed(s, 1, "rule_c")


def test_bare_ignore_suppresses_all():
    content = 'x = 1  # slopcheck: ignore\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "any_rule")
    assert is_suppressed(s, 1, "another_rule")


def test_js_style_comment():
    content = 'const x = 1; // slopcheck: ignore[stub_function_body_js]\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "stub_function_body_js")


def test_no_suppression():
    content = 'x = 1\ny = 2\n'
    s = parse_suppressions(content)
    assert not is_suppressed(s, 1, "any_rule")


def test_suppression_does_not_leak():
    content = '# slopcheck: ignore[rule_a]\nx = 1\ny = 2\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "rule_a")
    assert not is_suppressed(s, 2, "rule_a")


def test_ignore_next_targets_correct_line():
    content = 'ok\n# slopcheck: ignore-next[rule_a]\ntarget\nafter\n'
    s = parse_suppressions(content)
    assert not is_suppressed(s, 1, "rule_a")
    assert not is_suppressed(s, 2, "rule_a")
    assert is_suppressed(s, 3, "rule_a")
    assert not is_suppressed(s, 4, "rule_a")


def test_c_style_block_comment():
    content = 'x = 1; /* slopcheck: ignore[rule_x] */\n'
    s = parse_suppressions(content)
    assert is_suppressed(s, 1, "rule_x")


def test_scanner_integration(tmp_path):
    """Integration test: suppressed findings are excluded from scan results."""
    from slopcheck.config import AppConfig
    from slopcheck.engine.scanner import scan_paths

    # Create a file with a TODO that is suppressed
    src = tmp_path / "example.py"
    src.write_text(
        "x = 1  # TODO: fix this  # slopcheck: ignore[placeholder_tokens]\n"
        "y = 2  # TODO: and this\n"
    )
    config = AppConfig()
    result = scan_paths(repo_root=tmp_path, targets=None, config=config)

    # Only the unsuppressed TODO should appear
    todo_findings = [
        f for f in result.findings if f.rule_id == "placeholder_tokens"
    ]
    assert len(todo_findings) == 1
    assert todo_findings[0].location.line == 2
    assert result.stats.suppressed == 1

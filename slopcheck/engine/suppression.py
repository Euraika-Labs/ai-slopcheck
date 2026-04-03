"""Inline suppression comment parser.

Parses comments like:
  # slopcheck: ignore[rule_id]          (same-line, Python)
  // slopcheck: ignore[rule_a, rule_b]  (same-line, JS/TS/Go/C)
  # slopcheck: ignore-next[rule_id]     (applies to next line)
"""
from __future__ import annotations

import re

# Matches slopcheck suppression directives in any comment style.
# Group 1: "ignore" or "ignore-next"
# Group 2: comma-separated rule IDs (optional — bare ignore suppresses all)
SUPPRESSION_RE = re.compile(
    r"(?:#|//|/\*)\s*slopcheck:\s*(ignore(?:-next)?)"
    r"(?:\[([^\]]*)\])?"
)


def parse_suppressions(content: str) -> dict[int, set[str]]:
    """Parse inline suppression comments from file content.

    Returns a dict mapping 1-indexed line numbers to sets of suppressed
    rule IDs. An empty set means all rules are suppressed on that line.
    """
    suppressions: dict[int, set[str]] = {}
    lines = content.splitlines()

    for i, line in enumerate(lines):
        match = SUPPRESSION_RE.search(line)
        if match is None:
            continue

        directive = match.group(1)  # "ignore" or "ignore-next"
        rule_spec = match.group(2)  # "rule_a, rule_b" or None

        if rule_spec:
            rule_ids = {r.strip() for r in rule_spec.split(",") if r.strip()}
        else:
            rule_ids = set()  # empty = suppress all

        if directive == "ignore":
            target_line = i + 1  # 1-indexed, same line
        else:  # ignore-next
            target_line = i + 2  # 1-indexed, next line

        if target_line in suppressions:
            if not suppressions[target_line]:
                continue  # already suppressing all
            if not rule_ids:
                suppressions[target_line] = set()
            else:
                suppressions[target_line].update(rule_ids)
        else:
            suppressions[target_line] = rule_ids

    return suppressions


def is_suppressed(
    suppressions: dict[int, set[str]], line: int, rule_id: str
) -> bool:
    """Check if a finding at the given line is suppressed."""
    if line not in suppressions:
        return False
    rule_ids = suppressions[line]
    return len(rule_ids) == 0 or rule_id in rule_ids

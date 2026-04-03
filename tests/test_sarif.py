from __future__ import annotations

import json

from ai_slopcheck.models import (
    Confidence,
    Finding,
    Location,
    ScanResult,
    ScanStats,
    Severity,
)
from ai_slopcheck.output.sarif import render_sarif


def _make_result(findings: list[Finding]) -> ScanResult:
    return ScanResult(
        repo_root="/repo",
        stats=ScanStats(scanned_files=1, findings=len(findings)),
        findings=findings,
    )


def _make_finding(**kwargs) -> Finding:
    defaults = {
        "rule_id": "test_rule",
        "title": "Test",
        "message": "A test finding",
        "severity": Severity.WARNING,
        "confidence": Confidence.HIGH,
        "location": Location(path="src/main.py", line=10),
        "fingerprint": "abc123",
    }
    defaults.update(kwargs)
    return Finding(**defaults)


def test_sarif_valid_json():
    result = _make_result([_make_finding()])
    output = render_sarif(result)
    parsed = json.loads(output)
    assert parsed["version"] == "2.1.0"


def test_sarif_has_runs():
    result = _make_result([_make_finding()])
    parsed = json.loads(render_sarif(result))
    assert len(parsed["runs"]) == 1
    assert parsed["runs"][0]["tool"]["driver"]["name"] == "ai_slopcheck"


def test_sarif_maps_severity():
    result = _make_result([
        _make_finding(severity=Severity.ERROR),
        _make_finding(
            severity=Severity.NOTE,
            rule_id="note_rule",
            fingerprint="def456",
        ),
    ])
    parsed = json.loads(render_sarif(result))
    results = parsed["runs"][0]["results"]
    assert results[0]["level"] == "error"
    assert results[1]["level"] == "note"


def test_sarif_includes_location():
    result = _make_result([
        _make_finding(location=Location(path="src/app.ts", line=42))
    ])
    parsed = json.loads(render_sarif(result))
    loc = parsed["runs"][0]["results"][0]["locations"][0]
    phys = loc["physicalLocation"]
    assert phys["artifactLocation"]["uri"] == "src/app.ts"
    assert phys["region"]["startLine"] == 42


def test_sarif_includes_fingerprint():
    result = _make_result([_make_finding(fingerprint="sha256abc")])
    parsed = json.loads(render_sarif(result))
    fps = parsed["runs"][0]["results"][0]["fingerprints"]
    assert fps["slopcheck/v1"] == "sha256abc"


def test_sarif_includes_rules():
    result = _make_result([
        _make_finding(rule_id="rule_a", fingerprint="a"),
        _make_finding(rule_id="rule_b", fingerprint="b"),
    ])
    parsed = json.loads(render_sarif(result))
    rules = parsed["runs"][0]["tool"]["driver"]["rules"]
    rule_ids = {r["id"] for r in rules}
    assert rule_ids == {"rule_a", "rule_b"}


def test_sarif_empty_findings():
    result = _make_result([])
    parsed = json.loads(render_sarif(result))
    assert parsed["runs"][0]["results"] == []
    assert parsed["runs"][0]["tool"]["driver"]["rules"] == []


def test_sarif_includes_suggestion_as_fix():
    result = _make_result([
        _make_finding(suggestion="Fix this by doing X")
    ])
    parsed = json.loads(render_sarif(result))
    fixes = parsed["runs"][0]["results"][0]["fixes"]
    assert fixes[0]["description"]["text"] == "Fix this by doing X"

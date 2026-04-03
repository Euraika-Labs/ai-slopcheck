"""SARIF v2.1.0 output renderer for GitHub Security tab integration."""
from __future__ import annotations

import json

from slopcheck.models import ScanResult, Severity

SARIF_LEVEL_MAP = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.NOTE: "note",
}


def render_sarif(scan_result: ScanResult) -> str:
    """Render findings as SARIF v2.1.0 JSON."""
    rules_seen: dict[str, dict] = {}
    results: list[dict] = []

    for finding in scan_result.findings:
        if finding.rule_id not in rules_seen:
            rules_seen[finding.rule_id] = {
                "id": finding.rule_id,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
                "defaultConfiguration": {
                    "level": SARIF_LEVEL_MAP.get(
                        finding.severity, "warning"
                    )
                },
            }

        result: dict = {
            "ruleId": finding.rule_id,
            "level": SARIF_LEVEL_MAP.get(finding.severity, "warning"),
            "message": {"text": finding.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.location.path,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": finding.location.line,
                        },
                    }
                }
            ],
            "fingerprints": {
                "slopcheck/v1": finding.fingerprint,
            },
        }

        if finding.location.column is not None:
            loc = result["locations"][0]["physicalLocation"]
            loc["region"]["startColumn"] = finding.location.column

        if finding.suggestion:
            result["fixes"] = [
                {
                    "description": {"text": finding.suggestion},
                }
            ]

        results.append(result)

    sarif = {
        "$schema": (
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec"
            "/main/sarif-2.1/schema/sarif-schema-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "slopcheck",
                        "version": scan_result.version,
                        "informationUri": (
                            "https://github.com/euraika/slopcheck"
                        ),
                        "rules": list(rules_seen.values()),
                    }
                },
                "results": results,
            }
        ],
    }

    return json.dumps(sarif, indent=2)

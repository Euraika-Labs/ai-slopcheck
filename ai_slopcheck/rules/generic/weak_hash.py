from __future__ import annotations

import re
from pathlib import Path

from ai_slopcheck.config import AppConfig
from ai_slopcheck.models import Confidence, Finding, Severity
from ai_slopcheck.rules.base import Rule

# Python: hashlib.md5(...) or hashlib.sha1(...)
_PY_HASHLIB_RE = re.compile(r"\bhashlib\.(md5|sha1)\s*\(", re.IGNORECASE)
# Generic function call: md5(...) or sha1(...)
_GENERIC_HASH_RE = re.compile(r"\b(md5|sha1)\s*\(", re.IGNORECASE)
# JS/TS: crypto.createHash('md5') or crypto.createHash("sha1")
_JS_CRYPTO_RE = re.compile(
    r"crypto\.createHash\s*\(\s*['\"](?:md5|sha1)['\"]", re.IGNORECASE
)


class WeakHashRule(Rule):
    rule_id = "weak_hash"
    title = "Weak cryptographic hash function used (MD5 or SHA-1)"
    supported_extensions = {".py", ".js", ".ts", ".go", ".java"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.weak_hash
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        findings: list[Finding] = []

        for lineno, line in enumerate(content.splitlines(), start=1):
            matched = False
            evidence = line.strip()

            if ext == ".py":
                m = _PY_HASHLIB_RE.search(line)
                if m:
                    matched = True
                    algorithm = m.group(1).upper()
            if not matched:
                m = _JS_CRYPTO_RE.search(line)
                if m:
                    matched = True
                    algorithm = "MD5/SHA-1"
            if not matched:
                m = _GENERIC_HASH_RE.search(line)
                if m:
                    matched = True
                    algorithm = m.group(1).upper()

            if matched:
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Weak hash algorithm ({algorithm}) detected. "
                            "MD5 and SHA-1 are cryptographically broken and must not be used "
                            "for security-sensitive purposes."
                        ),
                        severity=Severity.WARNING,
                        confidence=Confidence.HIGH,
                        evidence=evidence,
                        suggestion=(
                            "Use SHA-256 or SHA-512 for cryptographic purposes. "
                            "For non-security checksums, document the intent clearly."
                        ),
                        tags=["security", "cryptography", "hash"],
                    )
                )

        return findings

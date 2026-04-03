from __future__ import annotations

import re
from pathlib import Path

from slopcheck.config import AppConfig
from slopcheck.models import Confidence, Finding, Severity
from slopcheck.rules.base import Rule
from slopcheck.rules.generic._manifest import (
    load_declared_dependencies,
    python_stdlib_names,
)

# Python: "import X" or "from X import Y" — capture top-level package name
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)"
)

# JS/TS: import ... from 'pkg' / require('pkg') — capture bare package name (no . or /)
_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?\s+from\s+|require\s*\()\s*['"]([^'"./][^'"]*?)['"]"""
)

# Go: import "pkg" (single) or inside import block — capture module path
_GO_IMPORT_RE = re.compile(r'^\s*(?:\w+\s+)?"([^"]+)"')

# Go imports that are part of stdlib: no dot in the first path segment
_GO_STDLIB_NO_DOT = re.compile(r"^[a-z][a-z0-9/]*$")

# JS/TS built-ins (Node.js core modules)
_NODE_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "dns", "domain", "events", "fs", "http", "http2",
    "https", "module", "net", "os", "path", "perf_hooks", "process", "punycode",
    "querystring", "readline", "repl", "stream", "string_decoder", "timers",
    "tls", "trace_events", "tty", "url", "util", "v8", "vm", "worker_threads",
    "zlib",
}

# JS/TS scoped package root e.g. @org/pkg -> "@org/pkg"
_JS_SCOPED_RE = re.compile(r"^@[^/]+/[^/]+")


def _js_package_root(spec: str) -> str:
    """Return the installable package name from an import specifier."""
    if spec.startswith("@"):
        m = _JS_SCOPED_RE.match(spec)
        return m.group(0) if m else spec
    return spec.split("/")[0]


def _is_local_js(spec: str) -> bool:
    """Check if a JS import is local (relative, path alias, or absolute)."""
    return (
        spec.startswith(".")
        or spec.startswith("/")
        or spec.startswith("@/")  # Next.js / Vite path alias
        or spec.startswith("~/")  # Common path alias
        or spec.startswith("#")  # Node.js imports map
    )


class UndeclaredImportRule(Rule):
    rule_id = "undeclared_import"
    title = "Import not declared in manifest"
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

    def scan_file(
        self,
        *,
        repo_root: Path,
        relative_path: str,
        content: str,
        config: AppConfig,
    ) -> list[Finding]:
        rule_config = config.rules.undeclared_import
        if not rule_config.enabled or not self.applies_to_path(relative_path):
            return []

        ext = Path(relative_path).suffix.lower()
        deps = load_declared_dependencies(repo_root)
        additional_allowed = {a.lower().replace("-", "_") for a in rule_config.additional_allowed}

        if ext == ".py":
            return self._scan_python(relative_path, content, deps, additional_allowed)
        if ext in {".js", ".jsx", ".ts", ".tsx"}:
            return self._scan_js(relative_path, content, deps)
        if ext == ".go":
            return self._scan_go(relative_path, content, deps)
        return []

    def _scan_python(
        self,
        relative_path: str,
        content: str,
        deps: set[str],
        additional_allowed: set[str],
    ) -> list[Finding]:
        stdlib = python_stdlib_names()
        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            m = _PY_IMPORT_RE.match(line)
            if not m:
                continue
            pkg = m.group(1).lower().replace("-", "_")
            # stdlib, local relative imports (can't tell from bare name alone),
            # or in additional_allowed
            if pkg in stdlib or pkg in additional_allowed:
                continue
            # If it's declared in the manifest or looks like a local module
            # (no manifest info available, so we check deps)
            if pkg in deps:
                continue
            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=lineno,
                    message=(
                        f"Package `{pkg}` is imported but not declared in "
                        "requirements.txt / pyproject.toml."
                    ),
                    severity=Severity.ERROR,
                    confidence=Confidence.HIGH,
                    evidence=line.strip(),
                    suggestion=(
                        f"Add `{pkg}` to your requirements.txt or pyproject.toml dependencies."
                    ),
                    tags=["undeclared-dependency", "python"],
                )
            )
        return findings

    def _scan_js(
        self,
        relative_path: str,
        content: str,
        deps: set[str],
    ) -> list[Finding]:
        findings: list[Finding] = []
        for lineno, line in enumerate(content.splitlines(), start=1):
            for m in _JS_IMPORT_RE.finditer(line):
                spec = m.group(1)
                if _is_local_js(spec):
                    continue
                pkg = _js_package_root(spec)
                if pkg in _NODE_BUILTINS or f"node:{pkg}" in _NODE_BUILTINS:
                    continue
                # Strip node: prefix
                bare = pkg.removeprefix("node:")
                if bare in _NODE_BUILTINS:
                    continue
                if pkg in deps:
                    continue
                findings.append(
                    self.build_finding(
                        relative_path=relative_path,
                        line=lineno,
                        message=(
                            f"Package `{pkg}` is imported but not declared in package.json."
                        ),
                        severity=Severity.ERROR,
                        confidence=Confidence.HIGH,
                        evidence=line.strip(),
                        suggestion=(
                            f"Run `npm install {pkg}` and commit the updated package.json."
                        ),
                        tags=["undeclared-dependency", "javascript"],
                    )
                )
        return findings

    def _scan_go(
        self,
        relative_path: str,
        content: str,
        deps: set[str],
    ) -> list[Finding]:
        findings: list[Finding] = []
        in_import_block = False
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped == "import (":
                in_import_block = True
                continue
            if in_import_block and stripped == ")":
                in_import_block = False
                continue

            is_single = stripped.startswith('import "')
            if not (in_import_block or is_single):
                continue

            m = _GO_IMPORT_RE.match(line)
            if not m:
                continue
            path = m.group(1)
            # stdlib: no dot in first segment
            if _GO_STDLIB_NO_DOT.match(path):
                continue
            # Check if any declared module is a prefix of this import path
            if any(path.startswith(dep) for dep in deps):
                continue
            findings.append(
                self.build_finding(
                    relative_path=relative_path,
                    line=lineno,
                    message=(
                        f"Import `{path}` is not declared in go.mod."
                    ),
                    severity=Severity.ERROR,
                    confidence=Confidence.HIGH,
                    evidence=line.strip(),
                    suggestion=(
                        f"Run `go get {path}` and commit the updated go.mod."
                    ),
                    tags=["undeclared-dependency", "go"],
                )
            )
        return findings

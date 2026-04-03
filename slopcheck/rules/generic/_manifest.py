from __future__ import annotations

import re
import sys
from pathlib import Path

# Go stdlib prefix — anything that doesn't contain a dot is stdlib
_GO_STDLIB_RE = re.compile(r"^[a-z][a-z0-9/]*$")


def _parse_requirements_txt(path: Path) -> set[str]:
    """Extract top-level package names from requirements.txt."""
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip version specifiers and extras: "requests>=2.0" -> "requests"
        name = re.split(r"[>=<!;\[\s]", line)[0].strip()
        if name:
            names.add(name.lower().replace("-", "_"))
    return names


def _parse_pyproject_toml(path: Path) -> set[str]:
    """Extract dependency names from pyproject.toml (no external parser needed)."""
    names: set[str] = set()
    text = path.read_text(encoding="utf-8")
    in_deps = False
    for line in text.splitlines():
        stripped = line.strip()
        # PEP 621: dependencies = [ ... ]
        if re.match(r"^dependencies\s*=\s*\[", stripped):
            in_deps = True
            continue
        # Poetry: [tool.poetry.dependencies]
        if re.match(r"^\[tool\.poetry\.dependencies\]", stripped):
            in_deps = True
            continue
        # End of list/section
        if in_deps and (stripped == "]" or stripped.startswith("[")):
            in_deps = False
            continue
        if in_deps:
            # "requests>=2.0" or requests = ">=2"
            m = re.match(r'^["\']?([A-Za-z0-9_.-]+)', stripped)
            if m and not stripped.startswith("#"):
                name = m.group(1).lower().replace("-", "_")
                if name not in ("python",):
                    names.add(name)
    return names


def _parse_package_json(path: Path) -> set[str]:
    """Extract dependency names from package.json."""
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        names.update(data.get(key, {}).keys())
    return names


def _parse_go_mod(path: Path) -> set[str]:
    """Extract module paths from go.mod require block."""
    names: set[str] = set()
    in_require = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require or stripped.startswith("require "):
            # "github.com/foo/bar v1.2.3" or "require github.com/foo/bar v1.2.3"
            m = re.match(r"(?:require\s+)?([^\s]+)", stripped)
            if m:
                names.add(m.group(1))
    return names


def load_declared_dependencies(repo_root: Path) -> set[str]:
    """Return the set of declared dependencies for the repository.

    For Python, returns normalised package names (lowercase, _ instead of -).
    For JS/TS, returns the raw package names from package.json.
    For Go, returns the full module paths from go.mod.

    The returned set is intentionally mixed-type; each rule must look up
    only the format that matches its ecosystem.
    """
    deps: set[str] = set()

    req = repo_root / "requirements.txt"
    if req.exists():
        deps.update(_parse_requirements_txt(req))

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        deps.update(_parse_pyproject_toml(pyproject))

    pkg = repo_root / "package.json"
    if pkg.exists():
        deps.update(_parse_package_json(pkg))

    gomod = repo_root / "go.mod"
    if gomod.exists():
        deps.update(_parse_go_mod(gomod))

    return deps


def python_stdlib_names() -> set[str]:
    """Return Python stdlib module names."""
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)  # type: ignore[attr-defined]
    # Fallback for Python < 3.10
    return set()

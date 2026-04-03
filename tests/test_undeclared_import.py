from __future__ import annotations

import json
from pathlib import Path

from slopcheck.config import AppConfig, UndeclaredImportConfig
from slopcheck.rules.generic.undeclared_import import UndeclaredImportRule


def _make_config() -> AppConfig:
    config = AppConfig()
    config.rules.undeclared_import = UndeclaredImportConfig(enabled=True)
    return config


def _scan(content: str, path: str = "src/service.py", repo_root: Path | None = None) -> list:
    rule = UndeclaredImportRule()
    return rule.scan_file(
        repo_root=repo_root or Path("/repo"),
        relative_path=path,
        content=content,
        config=_make_config(),
    )


# ---------------------------------------------------------------------------
# Python tests
# ---------------------------------------------------------------------------


def test_py_missing_package(tmp_path: Path) -> None:
    """An import with no manifest at all should be flagged."""
    findings = _scan("import requests\n", repo_root=tmp_path)
    assert len(findings) == 1
    assert "requests" in findings[0].message


def test_py_declared_in_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests>=2.28\n")
    findings = _scan("import requests\n", repo_root=tmp_path)
    assert len(findings) == 0


def test_py_stdlib_allowed(tmp_path: Path) -> None:
    # os and sys are always in stdlib
    findings = _scan("import os\nimport sys\n", repo_root=tmp_path)
    assert len(findings) == 0


def test_py_additional_allowed_typing(tmp_path: Path) -> None:
    # 'typing' is in the default additional_allowed list
    findings = _scan("import typing\n", repo_root=tmp_path)
    assert len(findings) == 0


def test_py_from_import_flagged(tmp_path: Path) -> None:
    findings = _scan("from boto3 import client\n", repo_root=tmp_path)
    assert len(findings) == 1
    assert "boto3" in findings[0].message


def test_py_from_stdlib_not_flagged(tmp_path: Path) -> None:
    findings = _scan("from pathlib import Path\n", repo_root=tmp_path)
    assert len(findings) == 0


def test_py_declared_in_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = [\n  \"httpx>=0.27\",\n]\n"
    )
    findings = _scan("import httpx\n", repo_root=tmp_path)
    assert len(findings) == 0


def test_py_multiple_missing(tmp_path: Path) -> None:
    content = "import pandas\nimport numpy\n"
    findings = _scan(content, repo_root=tmp_path)
    assert len(findings) == 2


def test_py_disabled(tmp_path: Path) -> None:
    config = AppConfig()
    config.rules.undeclared_import = UndeclaredImportConfig(enabled=False)
    rule = UndeclaredImportRule()
    findings = rule.scan_file(
        repo_root=tmp_path,
        relative_path="src/x.py",
        content="import requests\n",
        config=config,
    )
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# JS/TS tests
# ---------------------------------------------------------------------------


def test_js_missing_package(tmp_path: Path) -> None:
    findings = _scan(
        "import axios from 'axios';\n",
        path="src/api.ts",
        repo_root=tmp_path,
    )
    assert len(findings) == 1
    assert "axios" in findings[0].message


def test_js_declared_in_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"axios": "^1.0.0"}})
    )
    findings = _scan(
        "import axios from 'axios';\n",
        path="src/api.ts",
        repo_root=tmp_path,
    )
    assert len(findings) == 0


def test_js_local_import_skipped(tmp_path: Path) -> None:
    findings = _scan(
        "import { foo } from './utils';\n",
        path="src/api.ts",
        repo_root=tmp_path,
    )
    assert len(findings) == 0


def test_js_node_builtin_skipped(tmp_path: Path) -> None:
    findings = _scan(
        "import fs from 'fs';\n",
        path="src/api.ts",
        repo_root=tmp_path,
    )
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# Go tests
# ---------------------------------------------------------------------------


def test_go_missing_import(tmp_path: Path) -> None:
    code = 'import "github.com/gin-gonic/gin"\n'
    findings = _scan(code, path="main.go", repo_root=tmp_path)
    assert len(findings) == 1
    assert "gin-gonic" in findings[0].message


def test_go_declared_in_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text(
        "module example.com/myapp\n\nrequire github.com/gin-gonic/gin v1.9.0\n"
    )
    code = 'import "github.com/gin-gonic/gin"\n'
    findings = _scan(code, path="main.go", repo_root=tmp_path)
    assert len(findings) == 0


def test_go_stdlib_not_flagged(tmp_path: Path) -> None:
    code = 'import "fmt"\n'
    findings = _scan(code, path="main.go", repo_root=tmp_path)
    assert len(findings) == 0


def test_skips_non_matching_extension() -> None:
    rule = UndeclaredImportRule()
    findings = rule.scan_file(
        repo_root=Path("/repo"),
        relative_path="README.md",
        content="import requests\n",
        config=AppConfig(),
    )
    assert len(findings) == 0

from pathlib import Path

from slopcheck.config import AppConfig, BoundaryConfig, ForbiddenImportEdgesConfig, RulesConfig
from slopcheck.rules.repo.forbidden_import_edges import ForbiddenImportEdgesRule


def _make_config(
    *,
    source_glob: str = "src/controller.py",
    forbidden_prefixes: list[str] | None = None,
    message: str = "Controllers must not import the DB layer directly.",
    enabled: bool = True,
) -> AppConfig:
    """Helper to build an AppConfig with a single boundary."""
    return AppConfig(
        rules=RulesConfig(
            forbidden_import_edges=ForbiddenImportEdgesConfig(
                enabled=enabled,
                boundaries=[
                    BoundaryConfig(
                        source_glob=source_glob,
                        forbidden_prefixes=forbidden_prefixes or ["src.db"],
                        message=message,
                    )
                ],
            )
        )
    )


def test_forbidden_import_edges_rule_flags_python_boundary_violation() -> None:
    config = _make_config()

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from src.db import Database\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "forbidden_import_edges"
    assert findings[0].location.line == 1
    assert findings[0].severity.value == "error"


def test_forbidden_import_edges_rule_disabled_returns_nothing() -> None:
    config = AppConfig(
        rules=RulesConfig(
            forbidden_import_edges=ForbiddenImportEdgesConfig(
                enabled=False,
                boundaries=[
                    BoundaryConfig(
                        source_glob="src/controller.py",
                        forbidden_prefixes=["src.db"],
                    )
                ],
            )
        )
    )

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from src.db import Database\n",
        config=config,
    )

    assert findings == []


def test_forbidden_import_edges_no_boundaries_configured() -> None:
    """Default AppConfig has no boundaries, so nothing should fire."""
    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from src.db import Database\n",
        config=AppConfig(),
    )

    assert findings == []


def test_forbidden_import_edges_file_path_not_matching_glob_returns_nothing() -> None:
    """Scanning a file that does not match the source_glob produces no findings."""
    config = _make_config(source_glob="src/controller.py")

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/service.py",
        content="from src.db import Database\n",
        config=config,
    )

    assert findings == []


def test_forbidden_import_edges_bare_import_style() -> None:
    """'import src.db' (bare import) should trigger the rule."""
    config = _make_config()

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="import src.db\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "src.db"


def test_forbidden_import_edges_nested_submodule() -> None:
    """'from src.db.models import User' should trigger (starts with src.db.)."""
    config = _make_config()

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from src.db.models import User\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "src.db.models"


def test_forbidden_import_edges_exact_prefix_match_only() -> None:
    """'import src.dbc' should NOT trigger for prefix 'src.db' (not a prefix boundary)."""
    config = _make_config()

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="import src.dbc\n",
        config=config,
    )

    assert findings == []


def test_forbidden_import_edges_relative_import_resolved() -> None:
    """'from .db import Database' in 'src/controller.py' resolves to 'src.db' and triggers."""
    config = _make_config(source_glob="src/*.py", forbidden_prefixes=["src.db"])

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from .db import Database\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "src.db"


def test_forbidden_import_edges_multiple_violations_in_file() -> None:
    """Two violating imports should produce two findings."""
    config = _make_config()
    content = "from src.db import Database\nimport src.db.engine\n"

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content=content,
        config=config,
    )

    assert len(findings) == 2
    assert findings[0].location.line == 1
    assert findings[1].location.line == 2


def test_forbidden_import_edges_non_python_file_returns_nothing() -> None:
    """Non-Python files should be skipped by supported_extensions check."""
    config = _make_config(source_glob="src/*")

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="controller.ts",
        content="import { Database } from 'src/db';\n",
        config=config,
    )

    assert findings == []


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------


def test_forbidden_import_edges_bare_dot_import() -> None:
    """'from . import Database' in 'src/controller.py' resolves to the 'src' package."""
    config = _make_config(
        source_glob="src/*.py",
        forbidden_prefixes=["src"],
    )

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from . import Database\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "src"


def test_forbidden_import_edges_aliased_import() -> None:
    """'import src.db as db' should trigger — the alias does not hide the real module."""
    config = _make_config(
        source_glob="src/*.py",
        forbidden_prefixes=["src.db"],
    )

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="import src.db as db\n",
        config=config,
    )

    assert len(findings) == 1
    assert findings[0].evidence == "src.db"


def test_forbidden_import_edges_relative_import_above_root_returns_nothing() -> None:
    """Three-dot relative import from depth-2 goes above repo root."""
    config = _make_config(
        source_glob="src/*.py",
        forbidden_prefixes=["src"],
    )

    rule = ForbiddenImportEdgesRule()
    findings = rule.scan_file(
        repo_root=Path("."),
        relative_path="src/controller.py",
        content="from ...above import X\n",
        config=config,
    )

    assert findings == []

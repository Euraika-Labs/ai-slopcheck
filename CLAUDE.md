# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Build and test commands

```bash
# Install (editable, with dev deps)
pip install -e .[dev]          # or: uv pip install -e .[dev]

# Run all tests
pytest

# Run a single test file
pytest tests/test_placeholder_tokens.py

# Run a single test by name
pytest -k test_placeholder_scans_banned_tokens

# Lint
ruff check .

# Full quality gate (tests + lint)
make check

# Run scanner against fixture repo
make scan-fixture
# Or manually:
python -m slopcheck scan . --repo-root tests/fixtures/sample_repo --output /tmp/findings.json --fail-on none
python -m slopcheck summary /tmp/findings.json
python -m slopcheck github-annotations /tmp/findings.json
python -m slopcheck sarif /tmp/findings.json

# Create a baseline from findings
python -m slopcheck create-baseline /tmp/findings.json --output .slopcheck/baseline.json
```

## Architecture overview

**Product shape:** deterministic CLI scanner, no LLM calls, no backend. Runs in GitHub Actions: checkout → scan → findings.json → annotations + exit code.

**42 rules, 463 tests. Multi-language (Python, JS/TS, Go). Tree-sitter optional. SARIF output.**

**Data flow:** `cli.py` → `engine/scanner.py` (discovers files, threads, runs rules) → `models.py` (Finding/ScanResult Pydantic models) → `output/` (annotations, markdown summary, SARIF).

### Key modules

- **`models.py`** — The stable findings contract. `Finding`, `Location`, `ScanResult`, `ScanStats` are Pydantic models. Changes here affect everything downstream.
- **`config.py`** — YAML config loading. Searches `.slopcheck/config.yaml`, `.slopcheck.yaml`, `.slopcheck.yml`. 40 typed Pydantic config models, one per rule.
- **`engine/scanner.py`** — Orchestrator. Discovers files via `repo_files.py`, dispatches rules per-extension, runs via `ThreadPoolExecutor` (up to 8 workers), applies inline suppressions, returns `ScanResult`.
- **`engine/suppression.py`** — Parses `# slopcheck: ignore[rule_id]` and `# slopcheck: ignore-next[rule_id]` directives. Supports Python (`#`) and JS/Go (`//`) comment styles.
- **`engine/context_filter.py`** — Single-pass string/comment/regex context detector. No dependencies. Used as fallback when tree-sitter is not installed.
- **`parsers/treesitter.py`** — Optional tree-sitter adapter. Content-addressable parse cache (50-entry bounded dict). Returns `None` when tree-sitter grammars are not installed; rules fall back gracefully.
- **`rules/base.py`** — Abstract `Rule` base class. Each rule implements `scan_file(repo_root, relative_path, content, config) → list[Finding]`. Provides `build_finding()` helper and SHA-256 `fingerprint()`.
- **`rules/registry.py`** — `build_rules()` returns the list of all 42 active rule instances. New rules must be registered here.
- **`state/store.py`** — Baseline load/write for fingerprint-based suppression.
- **`output/sarif.py`** — SARIF v2.1.0 renderer for the GitHub Security tab.

### Rule system

Two categories in `rules/`:
- **`generic/`** — 41 cross-repo rules covering AI artifacts, security, JS/Node, Go, Python, cross-language patterns
- **`repo/`** — 1 architecture-specific rule (`forbidden_import_edges.py` enforces import boundaries)

To add a rule: create the rule class in the appropriate directory, register it in `registry.py`, add typed config in `config.py`, add tests + fixture files, update `docs/rule-authoring.md`.

Rules with noisy defaults are `enabled: false` in config (e.g., `deep_nesting`, `large_function`, `obvious_perf_drain`). Check the config default before enabling in CI.

### Config resolution

Config lookup order: explicit `--config` flag → `.slopcheck/config.yaml` → `.slopcheck.yaml` → `.slopcheck.yml` → defaults.

## Coding conventions

- Python 3.12+, type hints required.
- Pydantic models for all external contracts.
- Ruff: line-length 100, lint selects `E, F, I, UP, B`, double quotes, space indent.
- File paths are always relative to `repo_root` inside the engine.
- Fingerprints use `sha256(rule_id\x00path\x00line\x00evidence)` (null-byte separated).

## How to work in this repository

- Use plan mode for architecture changes, workflow changes, or multi-file refactors.
- Read the smallest useful set of docs before editing.
- Keep root instructions compact; detailed reference material lives under `docs/`.
- When touching rule files, also read the relevant files in `.claude/rules/`.
- Prefer implementing one complete vertical slice over sketching many partial layers.
- Update Markdown docs when the code contract changes.

## File-specific guidance

When editing these areas, read the corresponding docs first:

- `slopcheck/rules/**/*.py` → `docs/rule-authoring.md`
- `slopcheck/output/**/*.py` → `docs/github-integration.md`
- `slopcheck/github/**/*.py` → `docs/github-integration.md` and `docs/security-model.md`
- `examples/workflows/**/*.yml` → `docs/github-integration.md` and `docs/security-model.md`

## If the task is ambiguous

Default to the current product constraints:

- deterministic checks only
- no backend, no LLM calls
- GitHub-first
- simple Python CLI

### Git Flow Branching Model

All projects follow **Git Flow** with **semantic versioning** (SemVer `MAJOR.MINOR.PATCH`).

**Branch structure:**

| Branch | Purpose | Deploys to |
|--------|---------|------------|
| `main` | Production-ready code. Tagged with SemVer releases. | Production |
| `develop` | Integration branch for next release. All features merge here. | Staging |
| `feature/<name>` | New features. Branch from `develop`, merge back to `develop`. | — |
| `release/<version>` | Release prep. Branch from `develop`, merge to both `main` and `develop`. | Staging |
| `hotfix/<version>` | Emergency fixes. Branch from `main`, merge to both `main` and `develop`. | Production |

**Rules:**

- **Never commit directly to `main` or `develop`.** Always use feature/release/hotfix branches.
- **Always branch from `develop`** for new work: `git checkout -b feature/my-feature develop`
- **Tag `main`** with SemVer after every release or hotfix merge: `git tag -a v1.2.0 -m "v1.2.0"`
- **Delete feature branches** after merge to keep the repo clean.
- Before pushing, verify the remote: `git remote -v`

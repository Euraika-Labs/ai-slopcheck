# User Guide

## What is slopcheck?

slopcheck is a deterministic CLI scanner that catches common AI-style code failures in pull requests. It runs without an LLM, without a backend, and without a network connection. The scanner produces a `findings.json` file that drives annotations, summaries, and exit codes in CI.

It does not try to guess whether code was AI-generated. It looks for patterns that are often the result of incomplete AI output: stub function bodies, omission comments, conversational text left in source, hallucinated placeholder values, and a broad set of language-specific antipatterns.

---

## Installation

**pip:**
```bash
pip install ai-slopcheck
```

**pip editable install (from source):**
```bash
pip install -e .[dev]
```

**uv:**
```bash
uv pip install ai-slopcheck
# or editable:
uv pip install -e .[dev]
```

Python 3.12 or later is required.

### Optional: tree-sitter grammars

tree-sitter provides more accurate context detection (distinguishing code from strings/comments). It is optional — all rules fall back to the built-in `context_filter` when tree-sitter is not available.

```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-go
```

Supported grammars: Python, JavaScript/JSX, TypeScript/TSX, Go.

---

## First scan

```bash
# Scan the current directory
ai-slopcheck scan . --repo-root .

# View a summary
ai-slopcheck summary findings.json

# Or print GitHub-style annotations
ai-slopcheck github-annotations findings.json
```

The `findings.json` file contains the full scan result. See [Understanding findings](#understanding-findings).

---

## Understanding findings

Each finding in `findings.json` has the following fields:

| Field | Description |
|-------|-------------|
| `rule_id` | The rule that produced the finding (e.g., `stub_function_body`). |
| `title` | Short display title. |
| `message` | Human-readable description of what was found. |
| `severity` | `note`, `warning`, or `error`. Indicates impact if the finding is real. |
| `confidence` | `low`, `medium`, or `high`. Indicates certainty the finding is valid. |
| `location.path` | File path, relative to the repo root. |
| `location.line` | Line number (1-indexed). |
| `fingerprint` | SHA-256 hash of `rule_id + path + line + evidence`. Stable across reruns. |
| `suggestion` | How to fix the finding. |
| `evidence` | The matched text or short description of what was found. |
| `tags` | List of classification tags. |

**Severity vs confidence:** These are intentionally separate. Severity is about impact; confidence is about precision. A `hardcoded_secret` finding may be `error` severity and `high` confidence. A `dead_code_comment` finding is `note` severity and `medium` confidence. Neither scale implies the other.

---

## Setting up baselines for existing codebases

When you first introduce slopcheck to a codebase with existing issues, a baseline lets you say: "only fail on new findings." You commit the baseline and burn down the existing issues over time.

**Step 1: Run an initial scan without failing**

```bash
ai-slopcheck scan . --repo-root . --output findings.json --fail-on none
```

**Step 2: Create a baseline from all current findings**

```bash
ai-slopcheck create-baseline findings.json --output .slopcheck/baseline.json
```

**Step 3: Commit the baseline**

```bash
git add .slopcheck/baseline.json
git commit -m "chore: add slopcheck baseline"
```

**Step 4: Future scans only fail on new findings**

```bash
ai-slopcheck scan . --repo-root . --baseline .slopcheck/baseline.json --fail-on warning
```

To remove a baseline entry (accept a finding as resolved), delete its fingerprint from `.slopcheck/baseline.json` and regenerate when needed. To add new accepted issues to the baseline, run `create-baseline` again on the latest findings.

---

## Using inline suppression

Suppress individual findings without disabling the entire rule by adding a comment to the source file.

**Same-line suppression:**
```python
password = os.getenv("DB_PASSWORD", "devonly")  # slopcheck: ignore[hardcoded_secret]
```

```go
// slopcheck: ignore[go_ignored_error]
_ = conn.Close()
```

**Next-line suppression:**
```python
# slopcheck: ignore-next[stub_function_body]
def placeholder():
    pass
```

**Suppress all rules on a line:**
```python
x = "TODO"  # slopcheck: ignore
```

**Suppress multiple rules:**
```python
# slopcheck: ignore-next[bare_except_pass, placeholder_tokens]
```

Suppressed findings are counted in `stats.suppressed` and not included in the findings list. The `unused_suppression` meta-rule (registered but currently a no-op) is intended to flag directives that never matched anything.

Comment styles recognized: `#` (Python), `//` (JS/TS/Go/C), `/*` (C-style).

---

## Integrating with GitHub Actions

### Simple workflow

Save this as `.github/workflows/slopcheck.yml`:

```yaml
name: slopcheck-pr

on:
  pull_request:
  merge_group:

permissions:
  contents: read

jobs:
  slopcheck:
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install slopcheck
        run: pip install ai-slopcheck

      - name: Run scan
        run: |
          ai-slopcheck scan . --repo-root . --output findings.json --fail-on warning

      - name: Emit GitHub annotations
        if: always()
        run: ai-slopcheck github-annotations findings.json

      - name: Add job summary
        if: always()
        run: ai-slopcheck summary findings.json >> "$GITHUB_STEP_SUMMARY"

      - name: Upload findings artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: slopcheck-findings
          path: findings.json
```

The `if: always()` guards ensure annotations and summaries are emitted even when the scan fails.

### Using a baseline in CI

```yaml
      - name: Run scan
        run: |
          ai-slopcheck scan . \
            --repo-root . \
            --output findings.json \
            --baseline .slopcheck/baseline.json \
            --fail-on warning
```

### Hardened two-workflow topology

For repositories that need comment automation with write access, split into two workflows:

1. **Untrusted scan workflow** (`pull_request`): scans code, uploads findings artifact. No secrets, `contents: read` only.
2. **Trusted commenter workflow** (`workflow_run`): downloads artifact, posts comments. Has `pull-requests: write`.

See [docs/github-integration.md](github-integration.md) for the security rationale. Never run `pull_request_target` for the scan step.

---

## Diff-only scanning for CI

Scanning only changed files reduces CI time significantly on large repositories.

```bash
# Use git to find changed files (compares to HEAD~1)
ai-slopcheck scan . --repo-root . --changed-files git

# Use a file list (e.g., from a CI step that computes changed files)
ai-slopcheck scan . --repo-root . --changed-files @changed.txt
```

The `@file.txt` format reads one path per line, relative to `--repo-root`.

In a GitHub Actions workflow:

```yaml
      - name: Get changed files
        run: git diff --name-only HEAD~1 > changed.txt

      - name: Run scan on changed files
        run: |
          ai-slopcheck scan . \
            --repo-root . \
            --changed-files @changed.txt \
            --output findings.json \
            --fail-on warning
```

---

## Confidence filtering

Use `--min-confidence` to ignore low-confidence findings in CI and focus on high-signal issues:

```bash
# Only report medium or high confidence findings
ai-slopcheck scan . --repo-root . --min-confidence medium

# Only report high confidence findings
ai-slopcheck scan . --repo-root . --min-confidence high
```

This is useful when introducing the tool to a noisy codebase. Start with `--min-confidence high` and relax the filter over time.

---

## SARIF integration with GitHub Security tab

SARIF output can be uploaded to GitHub's Security tab, where findings appear as code scanning alerts.

In a workflow:

```yaml
      - name: Run scan
        run: ai-slopcheck scan . --repo-root . --output findings.json --fail-on none

      - name: Generate SARIF
        run: ai-slopcheck sarif findings.json > slopcheck.sarif

      - name: Upload to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: slopcheck.sarif
```

Note: SARIF upload requires `security-events: write` permission.

```yaml
permissions:
  contents: read
  security-events: write
```

See [docs/cli-reference.md](cli-reference.md#slopcheck-sarif) for the SARIF schema details.

---

## Tuning the scanner

### Disable noisy rules

If a rule produces too many false positives for your codebase, disable it in `.slopcheck/config.yaml`:

```yaml
rules:
  placeholder_tokens:
    enabled: false
```

### Adjust thresholds for opt-in rules

Opt-in rules like `deep_nesting` and `large_function` have configurable thresholds:

```yaml
rules:
  deep_nesting:
    enabled: true
    max_depth: 8     # more permissive than the default 6

  large_function:
    enabled: true
    max_lines: 150   # more permissive than the default 100
```

### Customize placeholder tokens

```yaml
rules:
  placeholder_tokens:
    banned_tokens:
      - TODO
      - FIXME
      - HACK
      - TEMPORARY
      - REMOVEME
      - WIP
```

### Enforce import boundaries

The `forbidden_import_edges` rule is a no-op without configuration. Configure it per your architecture:

```yaml
rules:
  forbidden_import_edges:
    enabled: true
    boundaries:
      - source_glob: "src/api/*.py"
        forbidden_prefixes:
          - src.db
        message: "API layer must not import DB layer directly."
```

### Exclude paths

Add project-specific paths to `ignored_paths` in addition to the defaults:

```yaml
ignored_paths:
  # ... keep the defaults ...
  - legacy/**
  - migrations/**
  - "**/codegen/**"
```

Full reference: [docs/configuration-guide.md](configuration-guide.md).

---

## Rule catalog

See [docs/rule-catalog.md](rule-catalog.md) for the complete catalog of all 72 rules, including per-rule config options, trigger examples, and false-positive notes.

# Getting Started

## Installation

```bash
pip install -e .
# Or with dev dependencies:
pip install -e .[dev]
```

### Optional: Tree-sitter (better precision)

```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-go tree-sitter-typescript
```

## First Scan

```bash
# Scan a project
slopcheck scan /path/to/project --output findings.json --fail-on none

# View summary
slopcheck summary findings.json

# View as GitHub annotations
slopcheck github-annotations findings.json

# View as SARIF (for GitHub Security tab)
slopcheck sarif findings.json
```

## Understanding Findings

Each finding has:
- **rule_id** — which rule triggered (e.g., `bare_except_pass_js`)
- **severity** — `note`, `warning`, or `error`
- **confidence** — `low`, `medium`, or `high`
- **location** — file path and line number
- **message** — what was found
- **suggestion** — how to fix it
- **evidence** — the matched text

## Setting Up Baselines

For existing codebases with many findings:

```bash
# Step 1: Full scan
slopcheck scan . --output findings.json --fail-on none

# Step 2: Create baseline from current findings
slopcheck create-baseline findings.json

# Step 3: Commit the baseline
git add .slopcheck/baseline.json

# Step 4: CI only fails on NEW findings
slopcheck scan . --baseline .slopcheck/baseline.json --fail-on warning
```

## GitHub Actions

```yaml
name: slopcheck
on: [pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install slopcheck
      - run: slopcheck scan . --output findings.json --fail-on warning
      - run: slopcheck github-annotations findings.json
      - run: slopcheck sarif findings.json > results.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: results.sarif }
```

## Diff-Only Scanning (faster CI)

```bash
# Only scan files changed in this PR
slopcheck scan . --changed-files git --fail-on warning
```

## Suppressing Findings

### Inline (per-line)
```python
password = get_secret()  # slopcheck: ignore[hardcoded_secret]
```

### Inline (next line)
```go
// slopcheck: ignore-next[go_ignored_error]
_ = conn.Close()
```

### By confidence level
```bash
# Only show HIGH and MEDIUM confidence findings
slopcheck scan . --min-confidence medium
```

## API Route Snapshots

```bash
# Create snapshot of all API routes
slopcheck api-snapshot --repo-root .

# CI: detect removed routes
slopcheck scan . --api-baseline .slopcheck/api-snapshot.json --fail-on error
```

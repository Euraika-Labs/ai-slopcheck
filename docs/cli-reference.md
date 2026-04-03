# CLI Reference

slopcheck is a deterministic CLI scanner. The runtime model is:

1. `ai-slopcheck scan` scans files and writes `findings.json`
2. `ai-slopcheck summary`, `ai-slopcheck github-annotations`, or `ai-slopcheck sarif` consume that JSON
3. The `scan` exit code decides pass or fail

## Global usage

```
python -m slopcheck [COMMAND] [OPTIONS]
```

Run `python -m slopcheck --help` for a list of commands, or `python -m slopcheck COMMAND --help` for command-specific help.

---

## ai-slopcheck scan

Scan a repository and write findings to JSON.

```
python -m ai-slopcheck scan [PATHS...] [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATHS` | Files or directories to scan. Optional; defaults to the repo root. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--repo-root PATH` | `.` (cwd) | Repository root. Used for relative paths in findings, config file lookup, and git operations. Resolved to an absolute path. |
| `--config PATH` | _(auto-detect)_ | Explicit config file. Skips the automatic config search. |
| `--output PATH` | `findings.json` | Write findings JSON to this file. Use `-` to print to stdout. Parent directories are created if missing. |
| `--baseline PATH` | _(none)_ | Suppress findings whose fingerprints are in this baseline file. |
| `--fail-on LEVEL` | `error` | Exit with code 1 when any finding is at or above this severity. Levels: `none`, `note`, `warning`, `error`. Use `none` to always exit 0. |
| `--min-confidence LEVEL` | `low` | Only report findings at or above this confidence level. Levels: `low`, `medium`, `high`. |
| `--changed-files SPEC` | _(none)_ | Restrict scanning to changed files only. See [Diff-only scanning](#diff-only-scanning). |
| `--jobs N` | `0` (auto) | Number of parallel worker threads. `0` means auto-detect up to 8. `1` forces sequential execution. |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings at or above `--fail-on` threshold, or `--fail-on none`. |
| `1` | One or more findings at or above `--fail-on` threshold. |

Rule execution errors are reported to stderr but do not change the exit code unless a finding was blocked.

### Diff-only scanning

Use `--changed-files` to scan only a subset of files:

- `--changed-files git` — runs `git diff --name-only HEAD~1` in `--repo-root` and scans those files
- `--changed-files @file.txt` — reads a newline-separated file list from `file.txt`

This is the recommended mode for CI on large repositories.

### Examples

```bash
# Full repository scan, fail on errors (default)
python -m ai-slopcheck scan . --repo-root .

# Write to a specific file, fail on any warning or error
python -m ai-slopcheck scan . --repo-root . --output /tmp/findings.json --fail-on warning

# Only report high-confidence findings
python -m ai-slopcheck scan . --repo-root . --min-confidence high

# Scan only changed files (CI mode)
python -m ai-slopcheck scan . --repo-root . --changed-files git --fail-on warning

# Scan with a baseline (suppress known issues)
python -m ai-slopcheck scan . --repo-root . --baseline .slopcheck/baseline.json

# Never fail (useful when introducing the tool)
python -m ai-slopcheck scan . --repo-root . --fail-on none

# Print JSON to stdout
python -m ai-slopcheck scan . --repo-root . --output -

# Parallel scan with 4 threads
python -m ai-slopcheck scan . --repo-root . --jobs 4
```

---

## ai-slopcheck summary

Print a Markdown summary of findings from a findings file.

```
python -m ai-slopcheck summary FINDINGS_FILE
```

Output goes to stdout. Pipe it to `$GITHUB_STEP_SUMMARY` for GitHub Actions job summaries.

### Example

```bash
python -m ai-slopcheck summary findings.json >> "$GITHUB_STEP_SUMMARY"
```

---

## ai-slopcheck github-annotations

Print GitHub workflow annotation commands from a findings file.

```
python -m ai-slopcheck github-annotations FINDINGS_FILE
```

Emits `::warning file=...::` and `::error file=...::` lines to stdout. GitHub Actions reads these and surfaces them as inline annotations on pull requests.

Annotations correspond to the severity of each finding:

| Severity | Annotation type |
|----------|----------------|
| `note` | `::notice` |
| `warning` | `::warning` |
| `error` | `::error` |

### Example

```bash
python -m ai-slopcheck github-annotations findings.json
```

---

## ai-slopcheck sarif

Print SARIF v2.1.0 JSON from a findings file.

```
python -m ai-slopcheck sarif FINDINGS_FILE
```

Output goes to stdout. SARIF can be uploaded to GitHub's Security tab (code scanning alerts) using the `github/codeql-action/upload-sarif` action.

### SARIF schema notes

The SARIF output conforms to SARIF v2.1.0 (`oasis-tcs/sarif-spec`).

Key fields in the output:

| SARIF field | Source |
|-------------|--------|
| `runs[].tool.driver.name` | `"slopcheck"` |
| `runs[].tool.driver.rules[].id` | `finding.rule_id` |
| `results[].ruleId` | `finding.rule_id` |
| `results[].level` | Mapped from `finding.severity` |
| `results[].message.text` | `finding.message` |
| `results[].locations[].physicalLocation.artifactLocation.uri` | `finding.location.path` |
| `results[].locations[].physicalLocation.region.startLine` | `finding.location.line` |
| `results[].fingerprints["slopcheck/v1"]` | `finding.fingerprint` |
| `results[].fixes[].description.text` | `finding.suggestion` (when present) |

Severity mapping:

| slopcheck severity | SARIF level |
|-------------------|-------------|
| `error` | `error` |
| `warning` | `warning` |
| `note` | `note` |

### Example

```bash
# Write SARIF to a file
python -m ai-slopcheck sarif findings.json > slopcheck.sarif

# Upload to GitHub Security tab (in a workflow)
python -m ai-slopcheck sarif findings.json > slopcheck.sarif
# then use: uses: github/codeql-action/upload-sarif@v3
#           with: sarif_file: slopcheck.sarif
```

---

## ai-slopcheck create-baseline

Create a baseline file from an existing findings file. Findings in the baseline are suppressed in future scans when passed via `--baseline`.

```
python -m ai-slopcheck create-baseline FINDINGS_FILE [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output PATH` | `.slopcheck/baseline.json` | Path to write the baseline file. Parent directories are created if missing. |

### Baseline file format

```json
{
  "version": 1,
  "fingerprints": [
    "4d9b4e2c...",
    "a27f1c90..."
  ]
}
```

Fingerprints are sorted and deduplicated. The file is human-readable and should be committed to the repository.

### Workflow

```bash
# 1. Run an initial scan (do not fail)
python -m ai-slopcheck scan . --repo-root . --output findings.json --fail-on none

# 2. Create a baseline from all current findings
python -m ai-slopcheck create-baseline findings.json --output .slopcheck/baseline.json

# 3. Commit the baseline
git add .slopcheck/baseline.json
git commit -m "chore: add slopcheck baseline"

# 4. Future scans only fail on NEW findings
python -m ai-slopcheck scan . --repo-root . --baseline .slopcheck/baseline.json --fail-on warning
```

See [docs/user-guide.md](user-guide.md) for the full adoption workflow.

# slopcheck Wiki

**Deterministic scanner for AI-style code failures. 72 rules. No LLM.**

## Quick Links

- [Getting Started](Getting-Started) — install, first scan, CI setup
- [Rule Catalog](Rule-Catalog) — all 72 rules with examples
- [Configuration](Configuration) — YAML config, per-rule options
- [CLI Reference](CLI-Reference) — all commands and flags
- [FAQ](FAQ) — common questions and troubleshooting
- [Architecture](Architecture) — how slopcheck works internally
- [Contributing](Contributing) — how to add rules and contribute

## What is slopcheck?

slopcheck catches code failures that are common in AI-generated or rushed code:

- **Stub functions** that return None/pass/... instead of real logic
- **AI instruction comments** like "implement this" left behind
- **Silent error handling** (empty catch blocks, swallowed exceptions)
- **Hardcoded secrets** and insecure defaults
- **JavaScript antipatterns** (await in loops, unguarded JSON.parse, loose equality)
- **Go antipatterns** (ignored errors, missing defer, wrong error wrapping)
- **Security risks** (SQL injection, XSS, ReDoS, obfuscated code)
- **API contract breaks** (removed routes, deprecated endpoints)

## Key Features

| Feature | Description |
|---------|-------------|
| 72 rules | AI detection, security, JS/Node, Go, Python, cross-language |
| 6 languages | Python, JS/TS, Go, C/C++, SQL, Markdown |
| Inline suppression | `# slopcheck: ignore[rule_id]` |
| SARIF output | GitHub Security tab integration |
| Diff-only mode | Scan only changed files in CI |
| Baselines | Suppress existing findings, fail only on new ones |
| API snapshots | Detect removed API routes |
| Tree-sitter | Optional AST-aware context detection |
| Threaded | Multi-core scanning with `--jobs N` |

## Numbers

- **793 tests**, 0 lint errors
- **~91% precision** on enabled-by-default rules
- **17,671 files** scanned across 12 production repos
- **602 API routes** detected on a single Next.js project
- Scan time: ~2-12s per repo

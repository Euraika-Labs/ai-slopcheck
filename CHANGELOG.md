# Changelog

All notable changes to slopcheck are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-04-03

### Added

**72 rules** across Python, JS/TS, Go, C/C++, SQL, and Markdown.

#### AI Code Failure Detection (15 rules)
- Stub function bodies (Python, JS/TS, Go)
- AI instruction comments ("implement this", "omitted for brevity")
- Silent exception handlers (Python, JS/TS, Go)
- AI conversational bleed ("Certainly!", markdown fences)
- AI identity refusal ("As an AI language model")
- Hallucinated placeholders (YOUR_API_KEY_HERE)

#### Security (7 rules)
- Hardcoded secrets, SQL injection, insecure defaults
- Weak hashing (MD5/SHA1), obfuscated code (eval/exec)
- IDOR risk, undeclared imports (opt-in)

#### JavaScript / Node.js (11 rules)
- await-in-loop, unguarded JSON.parse, unhandled promises
- Timer leaks, loose equality, XSS risk
- console.log in production, TypeScript any abuse
- React index key, async useEffect, ReDoS

#### Go (3 rules)
- Ignored errors, missing defer, error wrap %w

#### Cross-Language (17 rules)
- Cross-language idiom detection, SELECT *, debug code
- Assignment in conditional, unreachable code, deep inheritance
- Multiple classes per file, oversized classes, break in nested loops
- Contradictory null checks, lock without release
- Dangerous shell commands in markdown, use-after-free (C/C++)
- Many positional args, weak function names, redundant SQL indexes

#### Quality (9 rules, opt-in)
- Deep nesting, large functions, large files
- Param reassignment, short variable names
- Within-file duplication, stale comments
- Recursion without limit, division by zero risk

#### API Contract (1 rule)
- Route snapshot comparison, commented-out routes, deprecated endpoints

#### Infrastructure
- Inline suppression (`# slopcheck: ignore[rule_id]`)
- Diff-only scanning (`--changed-files git`)
- SARIF v2.1.0 output
- Confidence filtering (`--min-confidence`)
- Threaded scanning (`--jobs N`)
- Tree-sitter integration (optional)
- Baseline suppression (`create-baseline` + `--baseline`)
- API route snapshots (`api-snapshot` + `--api-baseline`)

#### Documentation
- Architecture docs with Mermaid diagrams
- CLI reference, configuration guide, user guide
- Rule catalog (72 rules), rule authoring guide
- 3 ADRs, security model, contributing guide

### Benchmarks
- 17,671 files across 12 production repositories
- 793 tests, 0 lint errors
- ~91% precision on enabled-by-default rules
- 602 API routes detected on aegis-nextjs

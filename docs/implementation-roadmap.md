# Implementation Roadmap

This roadmap is intentionally ordered as vertical slices. Each milestone should produce a runnable, testable improvement.

## Milestone 0 — foundation

Status: started in this skeleton.

Deliverables:

- Python package layout
- typed findings model
- config loader
- working CLI
- unit tests
- basic docs
- GitHub annotation renderer
- one generic rule
- one repo-style rule

Exit criteria:

- `pytest` passes
- `ruff check .` passes
- `python -m slopcheck scan ...` works locally

## Milestone 1 — stable findings and exit behavior

Focus:

- make findings ordering deterministic
- make exit behavior easy to reason about
- lock the JSON contract enough for workflow use

Suggested work:

- explicit versioning for output
- robust sorting
- clearer summary counts
- better severity-based failing rules

## Milestone 2 — baseline and suppressions

Focus:

- allow teams to adopt the tool incrementally

Suggested work:

- baseline file format
- suppression file format
- fingerprint strategy
- CLI commands to create and refresh a baseline
- tests proving fingerprint stability

Exit criteria:

- scanner can hide known findings through a local file
- baseline behavior is documented
- finding fingerprints remain stable across trivial reruns

## Milestone 3 — diff-aware scanning

Focus:

- reduce noise and runtime for pull requests

Suggested work:

- collect changed files from GitHub context
- optionally limit rules to changed lines or hunks
- retain a scan-all mode for local debugging
- make diff parsing testable without GitHub Actions

Exit criteria:

- scanner can run against a file list
- scanner can optionally narrow results to changed lines
- docs explain the tradeoffs between scan-all and diff-only modes

## Milestone 4 — better repo rules

Focus:

- add rules that encode architectural intent

Suggested work:

- better forbidden edge matching
- config schema for boundary maps
- path-scoped rule config
- examples for common repo constraints

Exit criteria:

- at least three repo-style rules exist
- config examples are usable
- tests cover both positive and negative cases

## Milestone 5 — parser-backed precision

Focus:

- use Tree-sitter only where it clearly improves precision

Suggested work:

- parser adapter layer
- one precise AST-backed rule
- fallback behavior when parser extras are not installed
- benchmark docs for regex versus parser-backed matching

Exit criteria:

- one parser-backed rule is working and tested
- parser integration remains optional
- docs explain when parser-backed rules are worth the cost

## Milestone 6 — hardened GitHub integration

Focus:

- separate untrusted scanning from trusted commenting

Suggested work:

- artifact output
- trusted follow-up workflow
- summary posting
- permissions model
- explicit security tests or dry-run fixtures

Exit criteria:

- example workflows are documented
- privileged commenting never executes untrusted code
- repository permissions are minimal and explained

## Milestone 7 — packaging and adoption

Focus:

- make the tool easy to drop into other repos

Suggested work:

- cleaner CLI help
- packaged example config
- example workflows that work with minimal edits
- release process docs
- changelog discipline

## Milestone 8 — performance and polish

Focus:

- speed, stability, and maintainability

Suggested work:

- avoid rereading unchanged files
- cache expensive parser setup
- improve summary output
- add SARIF export if private-repo licensing is acceptable in the target environment

## What not to do early

Do not jump to these too early:

- central dashboard
- fleet-wide policy service
- web UI
- generalized plugin marketplace
- fuzzy scoring model
- model-based subjective review loop

## Recommended agent workflow

A coding agent should usually:

1. read `AGENTS.md`
2. read the relevant architecture docs
3. write an ExecPlan for Milestone 2 or larger work
4. implement one vertical slice
5. run tests
6. update docs
7. stop with a repo state that a human can understand immediately

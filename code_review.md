# Code Review Guide

This file is the shared review rubric for `slopcheck`.

The goal of review is not “clean code” in the abstract. The goal is to make sure the scanner becomes a trustworthy tool that catches real issues with low noise and predictable behavior.

## Review priorities

Review in this order:

1. correctness
2. safety
3. false-positive control
4. contract clarity
5. testability
6. maintainability
7. ergonomics

## General review questions

Ask these questions on every non-trivial change:

- Does the new behavior match the documented intent?
- Is the change obvious to a new maintainer?
- Can the behavior be tested without GitHub infrastructure?
- Does the code accidentally widen scope beyond the current product shape?
- Does the change make it easier or harder to reason about failures?

## Rule review checklist

For every new or modified rule, check:

- Does the rule have a crisp problem statement?
- Is the trigger logic deterministic?
- Is the rule biased toward low noise?
- Does the rule expose enough evidence to explain the finding?
- Are the severity and confidence levels justified?
- Is the fingerprint stable enough to support future baselines?
- Are there fixture tests for both positive and negative cases?
- Does the rule belong in `generic/` or `repo/`?

## Findings contract checklist

When `Finding` or `ScanResult` changes, check:

- Are old fields preserved or intentionally migrated?
- Is the JSON output still easy to consume in workflows?
- Are relative paths consistent?
- Are timestamps and ordering deterministic enough for tests?
- Is the exit-code behavior still obvious?

## GitHub integration checklist

For workflow or GitHub-facing changes, check:

- Is the event choice safe for untrusted pull requests?
- Are permissions minimal?
- Are secrets avoided in the untrusted workflow?
- Is `github.event.pull_request.head.sha` used where true head SHA matters?
- Are annotation or summary outputs escaped safely enough?
- Is the privileged workflow, if any, clearly separated from code execution?

## Architecture checklist

For design changes, check:

- Did the change solve a real problem already visible in the codebase?
- Could the same result be achieved with a smaller abstraction?
- Is a new dependency actually paying for itself?
- Was documentation updated?
- Should the change have been driven by an ExecPlan?

## Documentation checklist

When behavior changes, check whether these need updates:

- `README.md`
- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/github-integration.md`
- `docs/rule-authoring.md`
- example config
- prompts if the recommended workflow changed

## Things to reject hard

Reject changes that do any of the following without a very strong reason:

- add LLM calls to the product
- add a backend or database
- make GitHub integration depend on `pull_request_target` code execution
- create a generic plugin system before enough real rules exist
- introduce hidden global state
- merge a new rule without tests
- move key intent from docs into private assumptions

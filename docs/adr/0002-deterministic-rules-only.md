# ADR 0002: Deterministic rules only in the product path

## Status

Accepted

## Context

The project is intended to catch AI-style coding failures, but we do not want the product itself to depend on model calls.

Model-based review can be impressive, but it introduces ambiguity, data egress, cost, and a harder-to-audit trust model.

## Decision

The product path for v1 will use deterministic checks only.

That includes:

- regex-based rules where appropriate
- path-aware repo rules
- parser-backed rules when precision is needed

It excludes:

- hosted LLM review
- local LLM review in the core scan path
- probabilistic quality scoring

## Consequences

### Positive

- predictable outputs
- easier tests
- easier adoption in locked-down environments
- no model credentials
- clearer security story

### Negative

- some subtle semantic issues will remain out of scope
- high-level style judgments are not addressed by the scanner
- more effort is needed to encode repo-specific intent as real rules

## Follow-up

If future experimentation adds model-assisted workflows, they should be optional sidecars, never the core enforcement path.

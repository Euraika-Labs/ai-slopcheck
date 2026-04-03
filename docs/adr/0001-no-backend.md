# ADR 0001: No backend for v1

## Status

Accepted

## Context

The product goal is a deterministic pull request scanner that is easy to adopt and safe to run on untrusted code.

A backend would enable some future capabilities, but it would also introduce operational complexity early.

## Decision

Version 1 will not use a backend, database, queue, or web service.

The scanner will run as a local CLI in GitHub Actions and produce file-based outputs.

## Consequences

### Positive

- lower operational complexity
- easier local development
- easier open-source adoption
- simpler security model
- clearer failure modes

### Negative

- no central dashboard
- no multi-repo aggregation
- no server-side memory
- richer workflow automation may need artifacts instead of stateful services

## Follow-up

Revisit this decision only if a clear product need appears that cannot be solved with files, artifacts, and local configuration.

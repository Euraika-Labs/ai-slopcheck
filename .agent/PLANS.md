# Execution Plans (ExecPlans)

This file defines the planning format for significant work in this repository.

An ExecPlan is a living design-and-implementation document that a coding agent can follow from research through delivery. The plan should be good enough that a new contributor can restart from the plan and the current working tree without hidden context.

## When to use an ExecPlan

Create an ExecPlan for any change that has meaningful uncertainty, spans multiple files, or changes a product contract.

In this repository, that usually means:

- introducing a new workflow topology
- adding baselines or suppressions
- adding Tree-sitter-backed parsing
- changing the findings model
- changing exit code semantics
- designing a non-trivial repo rule system
- large refactors across package boundaries

Small fixes do not need an ExecPlan.

## How to write one

Write in plain English prose. Be explicit. Assume the reader is new to the repository. Avoid hand-wavy “we will refactor this later” language.

The plan must explain:

- the problem
- the constraints
- the chosen design
- the alternatives considered
- the milestones
- the validation strategy
- the progress made
- surprises discovered during execution
- the final outcome

## Required sections

Every ExecPlan must contain these sections:

1. `Title`
2. `Purpose`
3. `Context`
4. `Constraints`
5. `Non-goals`
6. `Design`
7. `Milestones`
8. `Validation`
9. `Progress`
10. `Decision Log`
11. `Surprises & Discoveries`
12. `Outcomes & Retrospective`

## Requirements

### Purpose

State what user or product problem is being solved and why the change matters now.

### Context

Explain the current state of the relevant code, docs, and workflows. Link to the exact files that matter.

### Constraints

List the hard constraints that shape the design. In this repo these often include:

- deterministic checks only
- no backend
- GitHub-first
- low false-positive tolerance
- simple Python CLI
- minimal permissions in workflows

### Non-goals

Name things that are intentionally excluded. This prevents silent scope creep.

### Design

Describe the design in prose first. Add code snippets, JSON examples, or diagrams only where they make the plan clearer.

### Milestones

Milestones should be vertical slices. Each milestone should leave the repo in a runnable state.

### Validation

State exactly how the work will be validated. Prefer concrete commands and expected outcomes.

### Progress

This is mandatory and must stay current while implementing. Use checkboxes here.

### Decision Log

Record meaningful design decisions and why they were made.

### Surprises & Discoveries

Record anything learned during implementation that changed the plan, invalidated an assumption, or exposed a hidden dependency.

### Outcomes & Retrospective

Explain what shipped, what did not, and what should happen next.

## Template

Copy this template into a new Markdown file when needed.

```md
# <Short plan title>

## Purpose

## Context

## Constraints

## Non-goals

## Design

## Milestones

### Milestone 1

### Milestone 2

### Milestone 3

## Validation

## Progress

- [ ] Research complete
- [ ] Design reviewed
- [ ] Milestone 1 shipped
- [ ] Milestone 2 shipped
- [ ] Milestone 3 shipped

## Decision Log

- Decision:
  Reason:

## Surprises & Discoveries

- <date>:
  Observation:
  Impact:

## Outcomes & Retrospective
```

## Repository-specific planning advice

In this repository, the best plans usually:

- separate rule-engine work from GitHub workflow work
- pin down data contracts early
- define how false positives will be limited
- say how fixture tests will be added
- explain how a change can fail safely

## Anti-patterns

Do not write plans that:

- just restate the task
- list files without explaining relationships
- skip validation
- say “implement X” without explaining how
- assume a future backend or service
- use “AI” as a substitute for a real rule design

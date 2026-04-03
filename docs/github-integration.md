# GitHub Integration

## Goal

The scanner should work well in GitHub pull requests without a backend.

## Integration levels

There are two useful levels.

### Level 1 — simple mode

One `pull_request` workflow:

- checks out the PR code
- runs `slopcheck`
- emits annotations
- writes a job summary
- fails or passes based on findings

This is the best starting point.

### Level 2 — hardened mode

Two workflows:

1. untrusted `pull_request` scan workflow
2. trusted `workflow_run` comment workflow

The first workflow scans and uploads artifacts.
The second reads the artifacts and posts comments or richer summaries.

Use this only when you need write access from automation.

## Why start with `pull_request`

It is the correct place to run code from the pull request branch.

The scanner should assume this workflow runs on untrusted code and therefore should:

- avoid secrets
- avoid write permissions
- avoid external side effects

## Why not use `pull_request_target` for scanning

`pull_request_target` runs in the context of the base repository. That makes it useful for trusted operations, but dangerous for executing untrusted pull request code.

This repo should treat `pull_request_target` as a trusted-control event, not as a place to run the PR's code.

## SHA handling

If a workflow needs the real head commit of the pull request, it should use the pull request event payload, not assume `GITHUB_SHA` is the head commit.

Design the integration helpers so this choice is explicit and easy to test.

## Initial workflow behavior

The first runnable workflow can scan all files. That keeps the implementation simple.

Later, the scanner should support:

- file-list scanning
- changed-line filtering
- merge queue support if needed

## Output modes

### Annotations

Annotations are the fastest path to value because they surface directly in the workflow logs and UI.

### Job summary

A Markdown summary is useful for grouped findings and overall counts.

### SARIF

SARIF is useful later, but should not block early delivery.

### Pull request comments

Comments should be optional and usually reserved for a trusted follow-up workflow.

## Permissions model

### Untrusted scan workflow

Typical permissions:

- `contents: read`

That is usually enough for checkout and scanning.

### Trusted follow-up workflow

Only if needed:

- `contents: read`
- `pull-requests: write`

Keep the privileged workflow separate from untrusted code execution.

## Artifact strategy

If you later split workflows, the artifact should contain at least:

- findings JSON
- summary Markdown
- minimal metadata such as repo, PR number, and head SHA

Keep the artifact schema simple and versioned.

## Example workflow progression

### Early example

- checkout code
- install package
- run `slopcheck scan`
- run `slopcheck github-annotations`
- append summary to `$GITHUB_STEP_SUMMARY`

### Later hardened example

- scan on `pull_request`
- upload findings artifact
- trusted `workflow_run` downloads artifact
- trusted workflow posts comment or review summary

## Security rule

Never trade away workflow safety just to get inline comments one milestone earlier.

## Recommended implementation order

1. annotations
2. Markdown summary
3. file-list scanning
4. diff-only filtering
5. artifact output
6. trusted follow-up commenter
7. SARIF

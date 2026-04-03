# Security Model

## Threat model

The scanner is designed to run on pull requests, including untrusted contributions.

That means the product must assume:

- repository content may be hostile
- file names may be weird
- comments and strings may contain shell-breaking text
- workflow outputs may be abused if not escaped carefully

## Security priorities

1. do not execute untrusted code in a trusted context
2. do not expose secrets in the scan workflow
3. do not grant write permissions unless truly needed
4. keep artifact and output handling simple
5. treat path handling and shell handling as attack surfaces

## Workflow model

### Safe default

Use an untrusted `pull_request` workflow with read-only permissions.

### Optional privileged workflow

If comments or richer automation need write access, use a trusted follow-up workflow that consumes artifacts but does not execute the pull request code.

## Dangerous pattern to avoid

Do not scan and execute pull request code inside a `pull_request_target` workflow.

That pattern collapses the trust boundary.

## Output handling

Annotations and summaries are useful, but they also carry untrusted content if you include source excerpts or raw messages.

Be careful to:

- escape workflow-command output
- avoid blindly echoing arbitrary file contents
- keep finding messages concise and structured
- avoid shell interpolation of untrusted strings

## Path handling

Always normalize paths relative to `repo_root`.

Do not trust user-provided or artifact-provided paths without checking that they remain inside the repository root.

## Artifact handling

If a later workflow reads findings artifacts:

- treat the artifact as untrusted input
- validate the JSON shape
- avoid feeding artifact data into shell commands without escaping
- keep the schema minimal

## Dependency discipline

Every dependency adds attack surface.

Prefer:

- small direct dependencies
- pure-Python dependencies when acceptable
- optional parser extras only when rules require them

## Security position on LLMs

The product must remain deterministic and local-first.

That is partly a product decision and partly a security decision:

- no API keys in the product path
- no prompt injection surface
- no data egress by default
- no ambiguity about which system made which decision

## Security review checklist

For security-sensitive changes, verify:

- event choice is safe
- workflow permissions are minimal
- no secrets appear in the scan path
- shell usage is safe
- paths are normalized
- output escaping is sufficient
- docs explain the trust model clearly

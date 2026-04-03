# State and Baselines

## Why this exists

A good scanner still needs an adoption path.

Most real repositories already contain issues. If the first run blocks everything forever, the tool will be disabled.

A baseline file lets a team say:

> “Only fail on new findings. We will burn down the old ones over time.”

## State philosophy

State should stay file-based in v1.

That means:

- no database
- no remote service
- no shared cache server

The repository and workflow artifacts are enough.

## Baseline design goals

A baseline system should be:

- human-readable
- easy to regenerate
- stable across reruns
- precise enough not to suppress unrelated findings

## Suggested baseline shape

A minimal design could be:

```json
{
  "version": 1,
  "fingerprints": [
    "4d9b4e2c...",
    "a27f1c90..."
  ]
}
```

A richer design may later add metadata such as:

- rule id
- path
- first seen date
- note
- owner

Start small.

## Suppressions versus baselines

They are different tools.

### Baseline

Use for existing accepted debt across a repo.

### Suppression

Use for a deliberate exception to a rule in a specific location.

Suppressions should usually require more explanation than a baseline entry.

## Suggested suppression shape

```yaml
suppressions:
  - rule_id: forbidden_import_edges
    path: src/legacy/controller.py
    line: 12
    reason: Legacy transition module scheduled for removal in Q3
```

## Fingerprint requirements

A fingerprint strategy should survive:

- rerunning the same scan
- minor unrelated edits elsewhere in the repo
- workflow environment differences

A fingerprint strategy will usually not survive large code motion perfectly. That is acceptable for v1.

## Migration strategy

If fingerprint semantics change later, version the baseline format and provide a regeneration path.

Do not silently reinterpret old fingerprints.

## Implementation notes

The current skeleton documents this state model but does not fully implement it yet.

Recommended next step:

- add fingerprint helpers
- add baseline loading
- add a CLI command to create a baseline from a findings file

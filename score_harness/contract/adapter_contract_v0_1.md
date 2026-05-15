# Adapter Contract v0.1

This contract defines the minimal integration interface between docs-as-code
consumers and the current harness implementation.

Scope: one backend only (`docs-as-code` harness). No framework switching is
required in v0.1.

## Design goals

- Keep the surface minimal and stable
- Keep execution deterministic and replayable
- Keep artifact locations machine-readable
- Keep governance linkage explicit (`issue_id` + run artifacts)

## Operations

Three operations are required:

1. `validate`
2. `run`
3. `report`

## Common request envelope

```json
{
  "contract_version": "v0.1.0",
  "operation": "validate",
  "issue_id": 1234,
  "task_spec": "score_harness/spec/task_001.json",
  "candidate_path": "score_harness/harness/base_harness.py",
  "artifacts_dir": ".stage/ISSUE-1234/harness",
  "profile": "iso26262",
  "strict": true
}
```

Field notes:

- `contract_version`: must be `v0.1.0`
- `operation`: one of `validate`, `run`, `report`
- `issue_id`: positive integer for issue-first traceability
- `task_spec`: path to one task file or task directory
- `candidate_path`: harness candidate entry file
- `artifacts_dir`: root directory for generated artifacts
- `profile`: currently fixed to `iso26262`
- `strict`: when true, fail on any contract or validation violation

## Common response envelope

```json
{
  "contract_version": "v0.1.0",
  "operation": "validate",
  "status": "pass",
  "error_code": null,
  "summary": "candidate validation completed",
  "artifacts": [
    {
      "path": ".stage/ISSUE-1234/harness/validation.json",
      "type": "validation_result"
    }
  ],
  "traceability": {
    "issue_id": 1234,
    "task_id": "task_001",
    "run_id": "20260515T101500Z_base_harness"
  }
}
```

## Status and errors

`status` must be one of:

- `pass`: operation completed and checks passed
- `fail`: operation completed but checks failed
- `error`: operation could not complete due to runtime/config/input issues

`error_code` must be null on `pass`; otherwise one of:

- `E_INPUT_INVALID`
- `E_CONTRACT_VERSION`
- `E_PROFILE_UNSUPPORTED`
- `E_CANDIDATE_INVALID`
- `E_TASK_SPEC_INVALID`
- `E_RUNTIME_FAILURE`
- `E_ARTIFACT_WRITE`

## Operation semantics

### validate

Expected behavior:

- Run cheap candidate validation (`validate_candidate.py`)
- Validate task spec readability/shape
- Emit validation artifact

### run

Expected behavior:

- Execute deterministic outer loop (`outer_loop.py`)
- Run Lane A gate per task
- Emit per-task trace artifacts and evolution summary artifacts

### report

Expected behavior:

- Read existing run artifacts only
- Return compact summary view
- No mutation of candidate code or task specs

## Artifact rules

- Prefer `.stage/ISSUE-<number>/...` for issue-scoped outputs
- Keep JSON artifacts small and grep-friendly
- Keep artifact names stable across runs

## Compatibility policy

- v0.1 is additive only
- New optional fields are allowed
- Required-field removals or semantic changes require v0.2+

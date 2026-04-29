# score-harness

Agent harness infrastructure for Eclipse S-CORE docs-as-code.

This directory is the integration gate between agent-generated changes and the
Lane A traceability gate (`scripts_bazel/traceability_gate.py`).

Treat this file as the entry map for the harness area. Keep it short. Put deeper
detail in the structured files below so agents can navigate selectively.

## Structure

```
score_harness/
  spec/                  Task specs (small, structured change scenarios)
  harness/               Harness candidates (one Python file per candidate)
  runs/                  Execution history (append-only, per iteration/candidate/task)
  consistency_rules.yaml Public docs-as-code rule catalog
  SKILL.md               Domain skill for the outer loop proposer
  outer_loop.py          Deterministic outer loop: run harness -> gate -> distill -> log
```

## Navigation

- Start here for the overall contract and command sequence
- Read `spec/` for task units and expected verdicts
- Read `consistency_rules.yaml` for rule IDs and impact semantics
- Read `outer_loop.py` for evaluation, distillation, and filesystem layout
- Read `SKILL.md` only when working on Lane B candidate evolution

## Lane A contract

Every harness candidate is evaluated against the same Lane A gate:

1. Run cheap candidate validation against one runnable task spec
2. For metrics_json tasks: load a stable `metrics.json` fixture directly
3. For needs_json tasks: use `metrics.json` from the same build directory as `needs.json` (both produced by Sphinx build)
4. Run `traceability_gate.py` with task-specific arguments to produce pass/fail verdict
5. Distill structured trace artifacts into `runs/<iteration>/<candidate>/traces/<task_id>/`

No LLM is required in Lane A. The outer loop is deterministic Python.

Note: `traceability_coverage.py` no longer exists as a separate script—coverage extraction is integrated into the Sphinx build via the score_metamodel extension.

## Queryability rules

- `runs/` is append-only
- trace artifacts must be JSON, small, and consistently named
- the proposer should start from `evolution_summary.jsonl` and then inspect only
  the traces it needs
- avoid raw stdout dumps as the primary artifact

## Lane B (optional)

A proposer (any coding agent) may read the trace history via `runs/` and
`evolution_summary.jsonl` and propose new harness candidates. Lane B never
determines merge eligibility.

## Getting started

```bash
# Validate a candidate cheaply before full evaluation
python3 score_harness/validate_candidate.py \
  --candidate score_harness/harness/base_harness.py \
  --task-spec score_harness/spec/task_002_threshold_fail.json

# Run the seeded gate-fixture corpus against the baseline harness
python3 score_harness/outer_loop.py \
  --candidate score_harness/harness/base_harness.py \
  --tasks score_harness/spec/

# Query prior runs, failed tasks, and candidate deltas
python3 score_harness/query_runs.py \
  --runs-dir score_harness/runs \
  --failed-tasks \
  --diff-candidates base_harness candidate_x
```

## Next implementation steps

1. Grow the seeded corpus beyond gate metrics fixtures to full docs build snapshots using the needs_json task path.
2. Add more candidate harnesses so run-to-run diffs show meaningful behavioral deltas.
3. Integrate the outer loop into CI as a non-blocking pre-gate pilot.

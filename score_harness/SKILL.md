---
name: score-harness-assurance
description: Run one iteration of assurance harness evolution for Eclipse S-CORE docs-as-code.
---

# Score Harness — Assurance Consistency Domain

Run ONE iteration of harness evolution. You analyze prior results, propose a new harness candidate, and implement it. The outer loop (`outer_loop.py`) handles evaluation.

## Critical constraints

- You MUST produce 1 new harness candidate every iteration.
- Do NOT hardcode task-specific knowledge. Harnesses must be general-purpose.
- Do NOT read raw `gate_stdout` fields from trace artifacts. Read only distilled JSON fields.
- One mechanism per candidate. If you are tempted to add "and also..." that is a second candidate.

## Safety and scope restrictions

**Harness candidates must comply with these mandatory rules:**

1. **File scope**: Candidates may only read files declared in the task spec's `input_path` or referenced by `consistency_rules`.
2. **No network access**: Candidates must not make HTTP requests, DNS lookups, or access external services.
3. **No side effects**: `get_context()` must be read-only. Write operations belong in `post_process()` if needed.
4. **Deterministic**: Same task spec + same candidate → same context. No timestamps, random values, or external state in context.
5. **Tool safety**: Candidates may import stdlib and repo-local modules only. No dynamic code execution via `eval()` or `exec()`.

**Violation consequences:**
- Candidates violating these rules will fail the cheap validation step before evaluation.
- Repeated violations may block future candidate submissions until governance review.

## Domain context

The task domain is: maintain ISO 26262 / ASPICE assurance arguments consistent with Sphinx-needs artifacts under change.

The Lane A evaluation sequence is:
1. `traceability_coverage.py --json-output` → metrics JSON
2. `traceability_gate.py` → pass/fail verdict
3. Structured trace artifacts written to `runs/<iteration>/<candidate>/traces/<task_id>/`

The harness variable is: what context is provided to the agent before it edits an RST file or needs.json.

## Key files

- `harness/base_harness.py` — base class and baseline candidate. Read before proposing.
- `evolution_summary.jsonl` — one line per prior candidate (read this first)
- `runs/` — trace history. Use grep to find patterns across tasks and iterations.
- `spec/*.json` — task specs defining input, expected verdict, and relevant consistency rules.

## Workflow

### Step 1: Analyze

1. Read `evolution_summary.jsonl` to understand what has been tried.
2. Read `runs/` traces for failed tasks: `impacted_elements.json` and `score.json`.
3. Read prior candidate harness files in `harness/`.
4. Form a falsifiable hypothesis: "Providing X before the agent acts will reduce Y failure class."

### Step 2: Implement

1. Copy `harness/base_harness.py` to `harness/<snake_case_name>.py`.
2. Override `get_context()` with your mechanism. Keep `post_process()` default unless needed.
3. Validate import: `python3 -c "from score_harness.harness.<name> import *; print('OK')"`.

### Step 3: Write pending_eval.json

```json
{
  "iteration": <N>,
  "candidates": [
    {
      "name": "<name>",
      "file": "harness/<name>.py",
      "hypothesis": "<falsifiable claim>",
      "mechanism": "<what get_context returns and why>",
      "expected_impact": "<which failure class should decrease>"
    }
  ]
}
```

Output: `CANDIDATE: <name>`

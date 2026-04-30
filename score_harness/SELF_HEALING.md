# Self-Healing Validation System

This system automatically learns from validation failures and feeds them back to the LLM proposer in future iterations.

## How It Works

### 1. Validation Runs Automatically

When `outer_loop.py` runs, it first validates the candidate harness:

```bash
python3 score_harness/outer_loop.py \
  --candidate score_harness/harness/my_candidate.py \
  --tasks score_harness/spec/ \
  --iteration 5
```

The validation checks:
- ✅ Harness interface (get_context, post_process)
- ✅ Linting (ruff)
- ✅ Type checking (basedpyright)
- ✅ Import succeeds
- ✅ Basic smoke test

### 2. Failures Are Logged

If validation fails (e.g., linting error, type error, missing method), the failure is automatically logged to **`validation_failures.jsonl`**:

```json
{"iteration": 5, "candidate": "my_candidate", "failure_type": "linting_error", "message": "F401 'json' imported but unused", "fix": "Run: ruff check --fix score_harness/harness/my_candidate.py"}
{"iteration": 6, "candidate": "another_candidate", "failure_type": "type_error", "message": "Type 'str | None' cannot be assigned to 'str'", "fix": "Fix type errors reported by basedpyright"}
```

### 3. Proposer Learns From Failures

In **Step 1** of the SKILL.md workflow, the LLM proposer is instructed to:

> **Read validation_failures.jsonl FIRST** — learn from past mistakes

Example mistakes the proposer will see:

| Iteration | Mistake | Fix Applied in Next Iteration |
|-----------|---------|-------------------------------|
| 3 | Forgot to import `Path` | Iteration 4: Add `from pathlib import Path` |
| 5 | Linting error: unused import | Iteration 6: Run `ruff check --fix` before submitting |
| 7 | Type error: `str | None` not handled | Iteration 8: Add null check |
| 9 | Forgot to run validation | Iteration 10: Always run `validate_candidate.py` |

### 4. System Self-Improves

Over iterations, the proposer builds a mental model of:
- Common validation failures
- How to prevent them
- Which checks to run before submitting

This is **learning without explicit training** — the feedback loop teaches the proposer through structured failure logs.

## Example: Learning From a Linting Mistake

**Iteration 3**: Proposer submits candidate with unused import
```python
# harness/candidate_3.py
import json  # ← unused
from pathlib import Path

class AssuranceHarness:
    def get_context(self, task_spec):
        return "context"
```

**Validation fails**:
```bash
[validation] FAILED: candidate_3 — 1 failures logged to validation_failures.jsonl
  - linting_error: Run: ruff check --fix score_harness/harness/candidate_3.py
```

**validation_failures.jsonl** records:
```json
{"iteration": 3, "candidate": "candidate_3", "failure_type": "linting_error", "message": "F401 'json' imported but unused", "fix": "Run: ruff check --fix score_harness/harness/candidate_3.py"}
```

**Iteration 4**: Proposer reads validation_failures.jsonl, sees the linting error, and now includes linting in Step 2:
```python
# harness/candidate_4.py
from pathlib import Path  # ← fixed: removed unused import

class AssuranceHarness:
    def get_context(self, task_spec):
        return "context"
```

**Validation passes** ✅

## Manual Validation

You can also run validation manually:

```bash
# Basic validation (interface checks only)
python3 score_harness/validate_candidate.py \
  --candidate score_harness/harness/my_candidate.py \
  --task-spec score_harness/spec/task_002_threshold_fail.json

# With failure logging
python3 score_harness/validate_candidate.py \
  --candidate score_harness/harness/my_candidate.py \
  --task-spec score_harness/spec/task_002_threshold_fail.json \
  --iteration 5 \
  --log-failures

# Skip external checks (for CI environments without ruff/basedpyright)
python3 score_harness/validate_candidate.py \
  --candidate score_harness/harness/my_candidate.py \
  --task-spec score_harness/spec/task_002_threshold_fail.json \
  --skip-external-checks
```

## Viewing Past Failures

```bash
# See all validation failures
cat score_harness/validation_failures.jsonl | jq .

# See failures from iteration 5
cat score_harness/validation_failures.jsonl | jq 'select(.iteration == 5)'

# See all linting errors
cat score_harness/validation_failures.jsonl | jq 'select(.failure_type == "linting_error")'

# Count failures by type
cat score_harness/validation_failures.jsonl | jq -r '.failure_type' | sort | uniq -c
```

## Why This Works Better Than Explicit Instructions

**Without self-healing**:
```markdown
Step 2: Implement
- Run linting
- Run type checking
- Run tests
- Run validation
```

❌ LLM might skip steps
❌ No feedback when steps are forgotten
❌ Instructions get stale

**With self-healing**:
```json
{"iteration": 3, "failure_type": "linting_error", "fix": "Run: ruff check --fix ..."}
{"iteration": 5, "failure_type": "type_error", "fix": "Fix type errors ..."}
```

✅ LLM sees **actual mistakes it made**
✅ Concrete fix instructions for each failure
✅ System learns over time
✅ Validation is enforced, not suggested

## Integration with CI

In CI environments, skip external checks if tools aren't installed:

```yaml
# .github/workflows/harness-validation.yml
- name: Validate harness candidates
  run: |
    python3 score_harness/validate_candidate.py \
      --candidate score_harness/harness/base_harness.py \
      --task-spec score_harness/spec/task_002_threshold_fail.json \
      --skip-external-checks  # Skip ruff/basedpyright in CI
```

Or install the tools:

```yaml
- name: Install validation tools
  run: pip install ruff basedpyright

- name: Validate with full checks
  run: |
    python3 score_harness/validate_candidate.py \
      --candidate score_harness/harness/base_harness.py \
      --task-spec score_harness/spec/task_002_threshold_fail.json
```

## Design Rationale

This approach is inspired by **Meta-Harness** but goes further:

| Meta-Harness | score_harness (with self-healing) |
|--------------|----------------------------------|
| Import validation only | Import + linting + type checking + interface validation |
| No failure logging | Failures logged to validation_failures.jsonl |
| LLM sees success/fail only | LLM sees exact failure reason + fix command |
| No learning across iterations | System learns from mistakes |

The key insight: **validation failures are training data**. By logging failures in a structured format, we enable the proposer to learn without manual instruction updates.

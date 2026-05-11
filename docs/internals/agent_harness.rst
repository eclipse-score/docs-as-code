..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License Version 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

Agent Harness
=============

The docs-as-code harness implementation lives under ``score_harness/``. It is a
maintainer-facing subsystem for evaluating harness candidates against
machine-readable change scenarios.

Subsystem map
-------------

The current subsystem layout is:

- ``score_harness/spec/``: task specifications used as evaluation units
- ``score_harness/harness/``: harness candidates, one Python file per candidate
- ``score_harness/outer_loop.py``: deterministic evaluation runner
- ``score_harness/validate_candidate.py``: cheap pre-benchmark validation
- ``score_harness/query_runs.py``: summary-first query helpers for prior runs
- ``score_harness/consistency_rules.yaml``: public rule catalog used by tasks and candidates
- ``score_harness/runs/``: append-only execution history and distilled traces

Execution flow
--------------

The execution contract is intentionally narrow:

1. Validate the candidate cheaply against one runnable task specification.
2. Load the candidate and task corpus.
3. Run the deterministic Lane A traceability gate for each active task.
4. Distill task-level trace artifacts into small JSON outputs.
5. Append a run-level summary entry to ``evolution_summary.jsonl``.

The outer loop is deterministic Python. No LLM is required in Lane A.

Artifacts
---------

A successful run writes:

- ``runs/<iteration>/<candidate>/score.json``
- ``runs/<iteration>/<candidate>/traces/<task_id>/gate_output.json``
- ``runs/<iteration>/<candidate>/traces/<task_id>/impacted_elements.json``
- ``runs/<iteration>/<candidate>/traces/<task_id>/score.json``
- ``runs/evolution_summary.jsonl``

If cheap validation fails, structured failure entries can also be appended to
``score_harness/validation_failures.jsonl`` so later iterations can avoid
repeating the same mistakes.

Manual and agent-assisted changes
---------------------------------

The harness is not limited to agent-generated changes. The important split is
not human versus agent, but deterministic versus optional.

- Lane A applies equally to manual changes and agent-assisted changes.
- Lane B is the optional agentic workflow for proposing and improving harness candidates.
- Merge eligibility remains tied to deterministic checks, not to the proposer.

Current CI status
-----------------

The harness is already covered indirectly by repository CI:

- linting covers harness files through repository-wide ``pre-commit`` execution
- Bazel test execution includes harness tests through ``bazel test //...``

What is not yet present is a dedicated harness workflow job that runs the outer
loop itself as a named CI check and uploads harness run artifacts.

That dedicated CI integration remains planned work.

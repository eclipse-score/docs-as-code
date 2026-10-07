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

Assurance Harness
=================

The deterministic harness evaluates the public rule catalog CR-001 through
CR-005 against needs snapshots and native gate fixtures. It provides no LLM
or automatic engineering approval. Its map is ``assurance/README.md``;
``assurance/corpus/index.json`` indexes 30 search and 10 heldout task specs.

Run ``bazel test //assurance:assurance_harness_test`` to exercise the complete
Lane A evaluation, coverage extraction, schema validation and trace queries.
Run ``bazel run //assurance:evaluate -- --validate-only`` for the cheap check.
For a baseline evaluation, supply a new output directory, for example
``bazel run //assurance:evaluate -- --output runs/001/baseline``.

The native metric functions calculate snapshot coverage with the selected
requirement-type and external-need scope. Prepared metrics fixtures retain their
counts and are explicitly labelled test seeds. Neither mode is historical
incident evidence. The unchanged traceability gate owns the verdict.

The outer loop writes meta.json and score.json plus four task trace files:
gate_output.json, impacted_elements.json, score.json and agent_diff.patch.
Task scores include coverage deltas and hash-bound execution provenance.
Start with evolution_summary.jsonl; ``assurance/query.py`` supports failed-task
queries and comparisons of indexed runs. Raw gate output is stored separately.

Candidates are reviewed Python programs. Static screening is cheap validation,
not a sandbox for arbitrary submitted code. The baseline rejects traversal,
symlinks, special files and oversized inputs, and treats documentation as inert
quoted data. The trusted checker reads authorized inputs independently of the
candidate's context. Phase 2 capability tokens, causal diagnostics and adaptive
rollback in score issue 2850 are separate post-MVP work.

Relationship to draft proposal 628
----------------------------------

This patch targets main at 102aad30bd373295d275722c3942b392a8eb7149.
Draft PR 628 at 4bc0fbfc83938cd9fa036d31f9f885f6ccde18c9 supplies a parallel
``score_harness`` proposal with three runnable fixture tasks. It is not merged
into this baseline. Maintainers should reconcile the namespace and loader API
before adopting both; this patch does not assert compatibility with that draft.

Native CI evaluates both splits on Python 3.12 and 3.14, then uploads
``assurance-runs-<python-version>`` with the index and structured traces.

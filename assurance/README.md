<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Deterministic assurance harness

This harness evaluates public change scenarios using the existing native traceability gate. The baseline candidate reads only explicitly authorized task inputs and rule references, emits stable context with content hashes, and calls no models or network services. CR-001 through CR-005 classify changes and retain direct impacts, graph propagation and invalidated evidence as distinct observations.

The [rule catalog](rules.json) and [task index](corpus/index.json) are queryable by rule and task ID. The corpus contains 30 search scenarios and 10 separately named heldout scenarios. They use executable native gate-test seeds and modeled argument snapshots; they are not production incident or safety-qualification evidence. Twenty search scenarios and the heldout seeds validate precomputed schema-v2 gate fixtures; ten additional search scenarios extract metrics from needs snapshots using the native metric functions. The CLI supports explicit requirement-type and external-need scope.

```bash
python -m assurance.runner --validate-only
python -m assurance.runner --output runs/001/baseline
python -m assurance.runner --split heldout --output runs/002/baseline
python -m assurance.query --store runs --failed
python -m scripts_bazel.traceability_coverage --needs-json path/to/needs.json --json-output metrics.json
python -m assurance.query --store runs --compare 001/baseline 002/baseline
bazel test //assurance:assurance_harness_test
```

The outer loop validates the candidate before evaluation, runs the unchanged native gate, validates metric and trace schemas, and distills task-level `gate_output.json`, `impacted_elements.json`, `score.json` and `agent_diff.patch`. Raw outputs remain separately under `raw/`. Start with `evolution_summary.jsonl`; the query helper lists candidate outcomes and failed tasks without packing all raw output into agent context. Provenance binds the candidate, gate, catalog, inputs and interpreter environment to each result. Output directories are immutable per evaluation; use a new iteration for reruns.

Candidate `input_files` is an explicit allowlist relative to `input_path`. Directory inputs require this list. Each input is a regular UTF-8 file no larger than 1 MiB; oversized files fail explicitly. Traversal and symlinks are rejected while opening every path component. Referenced rule files are separately authorized by the trusted task index. Documentation stays quoted data. `get_context()` has no write operations, network calls or model dependency; `post_process()` returns inert data and cannot authorize changes to gate options or paths.

Candidates are reviewed Python programs. Lightweight static screening rejects unsupported imports and obvious execution/write capabilities; it is not an arbitrary-code sandbox. Do not import a candidate extracted from documentation or an untrusted model response. The Phase 2 privilege, validation-attestation and rollback extensions in #2850 need their own threat-specific design; this MVP supplies no certification, qualification or automatic engineering acceptance.

The scenario evaluator consumes already prepared before/after snapshots. It performs no agent-driven edits. The patch trace describes those supplied snapshots; passing a seeded scenario does not show an agent fixed a real product defect.

Reusable goal, V&V solution and requirement-breakdown fragments are indexed in [blocks.json](blocks.json) and checked by `blocks.py`. Task specifications sit beside each scenario as `spec.md`. A trusted reader supplies check inputs independently of candidate context; candidates may return any deterministic context string.

The native Python 3.12/3.14 Bazel CI jobs evaluate both corpus splits and upload `assurance-runs-<python-version>` artifacts, including the evolution index and distilled traces. `assurance-runs/` and `runs/` are generated output directories excluded from Git.

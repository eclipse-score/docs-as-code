# Agent Entry Map

This file is the repository entrypoint for coding agents. It is intentionally
short. Treat it as a map, not an encyclopedia.

## What This Repo Does

- Builds and validates docs-as-code workflows for Eclipse S-CORE
- Maintains a Sphinx-needs metamodel and traceability tooling
- Provides Lane A validation for requirements, code links, and test links

## Where To Look First

- `README.md` - repository overview and main build/test flow
- `docs/` - user and internal documentation
- `scripts_bazel/traceability_coverage.py` - metrics extraction
- `scripts_bazel/traceability_gate.py` - deterministic Lane A gate
- `score_harness/README.md` - harness subsystem map and execution flow

## Core Commands

- Build docs / generate needs data: use the existing repo build flow from `README.md`
- Run traceability metrics: `python scripts_bazel/traceability_coverage.py --json-output <needs.json>`
- Run traceability gate: `python scripts_bazel/traceability_gate.py <needs.json>`
- Run Python tests: use the existing repo test command from `README.md`

## Harness Area

The harness subsystem lives under `score_harness/`.

- `score_harness/spec/` - task specs (small, structured change scenarios)
- `score_harness/harness/` - candidate harness code
- `score_harness/runs/` - append-only execution history
- `score_harness/outer_loop.py` - deterministic evaluation and trace distillation
- `score_harness/consistency_rules.yaml` - public rule catalog for docs-as-code

## Working Rules

- Keep Lane A deterministic and OSS-only
- Keep required artifacts machine-readable and grep-able
- Put recurring rules into tooling when possible, not only prose
- Keep top-level instruction files short; move detail into indexed files nearby
- Prefer additive, low-risk harness changes over broad prompt rewrites

## Public vs Internal Boundary

- Public issues: tooling, schemas, validators, workflows, public task corpora
- Internal work: release authority, confidential benchmarks, waivers, supplier/legal obligations

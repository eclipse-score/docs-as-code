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

.. _docs_agentic_software_development:

Agentic Software Development
============================

Docs-as-code can be developed with conventional manual changes or with
agent-assisted workflows. The key design rule is that agent assistance changes
how changes are proposed and analyzed, not how merge eligibility is decided.

Lane A and Lane B
-----------------

Lane A is the deterministic path. It validates candidate behavior and evaluates
change scenarios through the existing traceability gate. Lane A does not require
an LLM.

Lane B is optional. A coding agent may inspect prior structured traces and
propose improved harness candidates. Lane B can accelerate iteration, but it
never overrides a Lane A denial.

This means:

- manual and agent-assisted changes both converge on the same deterministic gate.
- optional agent reasoning is kept outside the merge-critical decision path.
- structured run artifacts are part of the design, not an afterthought.

Old approach vs harness-based approach
--------------------------------------

Without the harness, repository checks can still validate a change, but the
feedback surface is coarse: pass/fail results, scattered logs, and limited
structured evidence for iterative improvement.

With the harness, changes are evaluated through a staged workflow:

- cheap candidate validation first
- deterministic task execution through the Lane A gate
- distilled JSON trace artifacts for each task
- append-only summary history for future comparison and learning

Old approach flow
~~~~~~~~~~~~~~~~~

.. plantuml::

   @startuml
   title Old Approach: Repo Checks Without Harness Context

   hide footbox
   autonumber
   skinparam shadowing false

   actor "Developer / Agent" as DEV
   participant "Requirement / Docs Change" as REQ
   participant "Generic Repo Checks" as REPO
   participant "Review + CI Gate" as GATE

   DEV -> REQ : Edit requirement/docs/links
   REQ -> REPO : Trigger repo checks
   REPO -> REPO : Run lint/tests/traceability gate
   alt Checks fail
      REPO --> DEV : Coarse failure logs
      DEV -> REQ : Patch and retry
   else Checks pass
      REPO --> GATE : Pass/fail status + logs
      GATE --> DEV : Merge decision
   end

   @enduml

Harness-based flow
~~~~~~~~~~~~~~~~~~

.. plantuml::

   @startuml
   title Harness-Based Approach: Candidate + Smoke Validation + Structured Outputs

   hide footbox
   autonumber
   skinparam shadowing false

   actor "Developer / Agent" as DEV
   participant "Requirement Change" as REQ
   participant "Candidate\n(score_harness/harness/*.py)" as CAND
   collections "Agent Instructions\n(AGENTS.md)" as AGENTFILE
   collections "Skill Prompts\n(.github/instructions, SKILL.md)" as SKILLFILE
   collections "Consistency Rules\n(score_harness/consistency_rules.yaml)" as RULES
   collections "Task Specs\n(score_harness/spec/*.yaml)" as SPECS
   participant "Smoke Validation\n(validate_candidate.py)" as SMOKE
   participant "Outer Loop\n(outer_loop.py)" as LOOP
   participant "Lane A Gate\n(traceability_gate.py)" as GATE
   participant "Review + CI Gate" as CIGATE
   database "Run Artifacts\n(score_harness/runs/...)" as ART

   DEV -> REQ : Start from requirement update
   DEV -> CAND : Propose or edit candidate
   CAND -> AGENTFILE : Read operating constraints
   CAND -> SKILLFILE : Read workflow skills/instructions
   CAND -> RULES : Load deterministic consistency checks
   LOOP -> SPECS : Load seeded task corpus

   LOOP -> SMOKE : Validate candidate before expensive runs
   alt Smoke validation fails
      SMOKE -> ART : Append validation_failures.jsonl
      SMOKE --> DEV : Early fail with actionable reason
   else Smoke validation passes
      LOOP -> GATE : Execute deterministic Lane A per task
      GATE --> LOOP : Verdict + metrics
      LOOP -> ART : Write traces/<task_id>/... artifacts
      LOOP -> ART : Append evolution_summary.jsonl
      LOOP -> CIGATE : Submit evidence bundle + verdict
      CIGATE --> DEV : Merge decision (same gate authority)
   end

   note over ART
   Append-only summaries and traces enable
   comparison, replay, and self-healing loops.
   end note

   @enduml

Why the harness exists
----------------------

The harness adds a repeatable evaluation layer around docs-as-code change
scenarios. It exists to make change quality visible in machine-readable form and
make iterative improvement queryable over time.

The design goals are:

- deterministic merge-critical checks
- cheap rejection of malformed candidates
- structured traces rather than raw stdout as the primary evidence format
- selective navigation of prior runs through summary-first artifacts
- optional agent-assisted improvement without introducing an LLM dependency into Lane A

For the implementation details, see :doc:`../internals/agent_harness`.

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

Agentic Software Development
============================

Docs-as-code supports both manual and agent-assisted change workflows.
In both cases, merge-relevant decisions remain anchored in deterministic Lane A
checks.

What this means in practice:

- manual changes and agent-generated changes are subject to the same Lane A gate.
- Lane A is deterministic Python and open-source tooling; it decides pass/fail.
- Lane B is optional and can use a coding agent to propose or improve harness candidates.
- structured traces make failures inspectable and reusable instead of relying on raw command logs.

If you are new to this workflow, start with the concept overview at
:doc:`../concepts/agentic_software_development`.

If you maintain the harness implementation itself, continue with
:doc:`../internals/agent_harness`.

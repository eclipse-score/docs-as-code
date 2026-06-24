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

.. _docs_requirement_coverage:

Requirement Test Coverage
=========================

This page shows which requirements are linked to tests and which have code
links.
The numbers shown here come from the same ``score_metrics`` calculations used
by CI quality gates — they will always match.

Overall Coverage
----------------

.. needpie:: Overall Requirement Coverage (non-overlapping)
   :labels: Remaining (no links), Test Link Only, Code Link Only, Fully Linked (Both)
   :colors: #ca2828, #009ad2, #d26403, #37a12d
   :filter-func: score_metrics.sphinx_filters.get_non_overlapping_link_metrics

.. needpie:: Test Linkages
   :labels: Tests Not Linked, Tests Linked
   :colors: #ca2828, #37a12d
   :filter-func: score_metrics.sphinx_filters.get_metrics_with_first_value_total(tests:total,tests:linked_to_requirements)

Requirement → Test Traceability
-------------------------------

.. needtable:: All tool_req with Linkage Status
   :types: tool_req
   :columns: id;testlink;source_code_link;implemented
   :style: table

Test → Requirement Traceability
-------------------------------

.. needtable:: All Testcases with Covered Requirements
   :types: testcase
   :filter: result == "passed"
   :columns: name as "Testcase";fully_verifies;partially_verifies;test_type;derivation_technique
   :style: table

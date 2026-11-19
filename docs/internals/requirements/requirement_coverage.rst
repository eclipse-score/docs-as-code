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

This page shows which docs-as-code requirements are linked to its tests
and which have code links.

Overall Coverage
----------------

.. needpie:: Overall Requirement Coverage (non-overlapping)
   :labels: Remaining (no links), Test Link Only, Code Link Only, Fully Linked (Both)
   :colors: #ca2828, #009ad2, #d26403, #37a12d
   :filter-func: score_metrics.sphinx_filters.get_docs_as_code_requirement_coverage

.. needpie:: Test Linkages
   :labels: Tests Not Linked, Tests Linked
   :colors: #ca2828, #37a12d
   :filter-func: score_metrics.sphinx_filters.get_docs_as_code_test_linkages

Tool Requirements and Code Links
--------------------------------

.. needtable:: Docs-as-code tool requirements
   :types: tool_req
   :tags: docs-as-code-requirement
   :columns: id;source_code_link;implemented
   :style: table

Test → Requirement Traceability
-------------------------------

.. needtable:: All Testcases with Covered Requirements
   :filter-func: score_metrics.sphinx_filters.get_docs_as_code_passing_tests_with_coverage
   :columns: name as "Testcase";fully_verifies;partially_verifies;test_type;derivation_technique
   :style: table

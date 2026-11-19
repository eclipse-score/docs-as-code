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

.. _docs_tooling_verification:

Tooling Verification
====================

This page describes verification evidence for the docs-as-code tooling itself.
It is intentionally separate from tooling coverage so downstream quality signals
such as unit tests, future static analysis, and other verification evidence can
evolve independently from traceability support.

Overview
--------

.. needpie:: Test Results
   :labels: passed, failed, skipped
   :colors: green, red, orange

   'test-module-score_docs_as_code' in tags and result == 'passed'
   'test-module-score_docs_as_code' in tags and result == 'failed'
   'test-module-score_docs_as_code' in tags and result == 'skipped'

.. grid:: 2
   :class-container: score-grid

   .. grid-item-card::

      Failed Tests

      *Hint: this table is empty by definition, as PRs with failing tests are not allowed to be merged in docs-as-code repo.*

      No failing tests are expected in the current dataset.

   .. grid-item-card::

      Skipped / Disabled Tests

      *Hint: this table is empty by definition, as we do not allow skipped or disabled tests in docs-as-code repo.*

      No skipped or disabled tests are expected in the current dataset.


Testcase Metadata Overview
--------------------------

*Data is not filled out yet within the test cases.*

.. needpie:: Test Types Used In Testcases
   :labels: fault-injection, interface-test, requirements-based, resource-usage
   :legend:

   'test-module-score_docs_as_code' in tags and test_type == 'fault-injection'
   'test-module-score_docs_as_code' in tags and test_type == 'interface-test'
   'test-module-score_docs_as_code' in tags and test_type == 'requirements-based'
   'test-module-score_docs_as_code' in tags and test_type == 'resource-usage'


.. needpie:: Derivation Techniques Used In Testcases
   :labels: requirements-analysis, design-analysis, boundary-values, equivalence-classes, fuzz-testing, error-guessing, explorative-testing
   :legend:

   'test-module-score_docs_as_code' in tags and derivation_technique == 'requirements-analysis'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'design-analysis'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'boundary-values'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'equivalence-classes'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'fuzz-testing'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'error-guessing'
   'test-module-score_docs_as_code' in tags and derivation_technique == 'explorative-testing'


All passed Tests
----------------

.. needtable:: SUCCESSFUL TESTS - status and link
   :filter: result == "passed"
   :tags: test-module-score_docs_as_code
   :columns: name as "testcase";result;id as "link"

.. needtable:: SUCCESSFUL TESTS - verification mapping
   :filter: result == "passed"
   :tags: test-module-score_docs_as_code
   :columns: name as "testcase";fully_verifies;partially_verifies

.. needtable:: SUCCESSFUL TESTS - optional metadata
   :filter: result == "passed"
   :tags: test-module-score_docs_as_code
   :columns: name as "testcase";test_type;derivation_technique

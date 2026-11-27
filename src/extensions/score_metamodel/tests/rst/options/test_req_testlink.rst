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

.. test_metadata::
   :id: test_metadata__req_testlink
   :partially_verifies_list: tool_req__docs_test_link_testcase[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that every requirement type accepts a ``testlink`` attribute.

   * Each requirement type with a GitHub ``testlink``: no warning
   * A ``testlink`` that is not a GitHub link: warning, proving the attribute
     is validated rather than silently ignored

   Populating ``testlink`` from test case results is covered by the source code
   linker integration test.


.. Positive Tests: every requirement type accepts a testlink

.. stkh_req:: Stakeholder requirement with testlink
   :id: stkh_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_stkh.py#L1
   :expect_not: testlink

.. feat_req:: Feature requirement with testlink
   :id: feat_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_feat.py#L1
   :expect_not: testlink

.. comp_req:: Component requirement with testlink
   :id: comp_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_comp.py#L1
   :expect_not: testlink

.. aou_req:: Assumption of use requirement with testlink
   :id: aou_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_aou.py#L1
   :expect_not: testlink

.. gd_req:: Process requirement with testlink
   :id: gd_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_gd.py#L1
   :expect_not: testlink

.. tool_req:: Tool requirement with testlink
   :id: tool_req__test_link__ok
   :testlink: https://github.com/eclipse-score/example/blob/main/test_tool.py#L1
   :expect_not: testlink


.. Negative Test: testlink is validated

.. feat_req:: Feature requirement with invalid testlink
   :id: feat_req__test_link__bad
   :testlink: not-a-link
   :expect: feat_req__test_link__bad.testlink (not-a-link): does not follow pattern `^https://github.com/.*`.

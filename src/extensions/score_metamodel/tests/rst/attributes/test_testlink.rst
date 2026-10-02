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


.. test_metadata:: Test Testlink Attribute
   :id: test_metadata__testlink_attribute
   :partially_verifies_list: tool_req__docs_test_link_testcase
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that requirements accept valid test links and reject malformed URLs.


.. stkh_req:: Valid Test Link
   :id: stkh_req__testlink__valid
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :rationale: Valid test link
   :valid_from: v1.0
   :testlink: https://github.com/eclipse-score/docs-as-code
   :expect_not: does not follow pattern


.. stkh_req:: Invalid Test Link
   :id: stkh_req__testlink__invalid
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :rationale: Invalid test link
   :valid_from: v1.0
   :testlink: http://github.com/eclipse-score/docs-as-code
   :expect: does not follow pattern

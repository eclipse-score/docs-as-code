..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
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


.. test_metadata:: Test ID scheme
   :id: test_metadata__check_id_scheme
   :fully_verifies_list: tool_req__docs_common_attr_id_scheme
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests all aspects of the need ID naming scheme:
   - Correct number of ``__``-separated parts per need type
   - Feature/structural part matching the file path
   - Option regex patterns (e.g. external link prefixes)


.. ## Part-count checks


.. stkh_req:: This is a test
   :id: stkh_req__test
   :expect: stkh_req__test.id (stkh_req__test): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.


.. stkh_req:: This is a test
   :id: stkh_req__test__abcd
   :expect_not: expected to consist of this format


.. stkh_req:: This is a test
   :id: stkh_req__test__test__abcd
   :expect: stkh_req__test__test__abcd.id (stkh_req__test__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.


.. workproduct:: This is a test
   :id: wp__test__abcd
   :expect: wp__test__abcd.id (wp__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>`.


.. workproduct:: This is a test
   :id: wp__test
   :expect_not: expected to consist of this format


.. ## Feature-in-path checks (from id_contains_feature)


.. std_wp:: This is a test
   :id: std_wp__attributes__abce
   :expect_not: Feature 'attributes' not in path


.. std_wp:: This is a test
   :id: std_wp__test1__test2__abce
   :expect_not: not in path


.. stkh_req:: This is a test
   :id: stkh_req__test__abce
   :expect_not: Feature 'test' not in path


.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__abcabc__testing
   :expect: Feature part 'abcabc' not found in path 'attributes'.


.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__attributes__testing
   :expect_not: Feature part


.. feat_req:: Testing conf.py parameter
   :id: feat_req__blabla__testing
   :expect_not: Feature part


.. feat_req:: Testing conf.py parameter
   :id: feat_req__abcabcabc__blabla_testing
   :expect: Feature part 'abcabcabc' not found in path 'attributes'.


.. ## option values follow their metamodel-defined regex patterns.


.. tool_req:: This is a test
   :id: tool_req__test_abcd
   :satisfies: doc_getstrt__req__process
   :expect_not: does not follow pattern `^doc_.+$`.

   This should not give a warning


.. tool_req:: This is a test
   :id: tool_req__test_aaaa
   :satisfies: doc_getstrt__req__process;gd_guidl__req__engineering
   :expect_not: does not follow pattern `^doc_.+$`., does not follow pattern `^gd_.+$`.

   This should give a warning

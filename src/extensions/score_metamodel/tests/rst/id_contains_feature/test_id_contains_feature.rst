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


.. test_metadata:: Title for metadata
   :id: test_metadata__id_contains_feature
   :partially_verifies_list: tool_req__docs_common_attr_id_scheme
   :test_type: requirements_test
   :derivation_technique: requirements_based
   :check: id_contains_feature

   This is the content


.. Feature is in the path of the RST file

.. std_wp:: This is a test
   :id: std_wp__id_contains_feature__abce
   :expect_not: Feature 'id_contains_feature' not in path


.. Check if the feature is in the path of the RST file is skipped,
   because the id contains 4 parts

.. std_wp:: This is a test
   :id: std_wp__test1__test2__abce
   :expect_not: not in path


.. Check if the feature is in the path of the RST file is skipped,
   because the requirement type is stkh_req

.. stkh_req:: This is a test
   :id: stkh_req__test__abce
   :expect_not: Feature 'test' not in path



.. Check if feature is correctly found to not be in path

.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__abcabc__testing
   :expect: Feature part 'abcabc' not found in path 'id_contains_feature'.



.. Check if feature is correctly found to be in path

.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__id_contains__testing
   :expect_not: Feature part


.. Testing if additional allowed param in conf.py is valid

.. feat_req:: Testing conf.py parameter
   :id: feat_req__blabla__testing
   :expect_not: Feature part


.. Testing if additional allowed param in conf.py is valid

.. feat_req:: Testing conf.py parameter
   :id: feat_req__abcabcabc__blabla_testing
   :expect: Feature part 'abcabcabc' not found in path 'id_contains_feature'.

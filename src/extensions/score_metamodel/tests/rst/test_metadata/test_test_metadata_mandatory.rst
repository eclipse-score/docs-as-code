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


.. test_metadata:: Testcase Metadata Validation
   :id: test_metadata__testcase_validation
   :fully_verifies_list:
      tool_req__docs_test_metadata_mandatory_1[version==1],
      tool_req__docs_test_metadata_mandatory_2[version==1],
      tool_req__docs_test_metadata_link_levels[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Verifies that testcase needs from test.xml files have mandatory metadata
   and correct link levels.


.. Setup: target needs for link-level tests

.. feat_req:: Valid feature requirement target
   :id: feat_req__testcase__abcd
   :version: 1
   :status: valid
   :safety: QM
   :security: NO


.. comp_req:: Valid component requirement target
   :id: comp_req__testcase__abcd
   :version: 1
   :status: valid
   :safety: QM
   :security: NO


.. testcase:: Missing test_type and derivation_technique
   :id: testcase__test_metadata__aaa1
   :version: 1
   :expect: testcase__test_metadata__aaa1: is missing required attribute: `test_type`.,
      testcase__test_metadata__aaa1: is missing required attribute: `derivation_technique`.,
      testcase__test_metadata__aaa1: is missing required attribute: `content`.



.. testcase:: Missing test_type only
   :id: testcase__test_metadata__aaa2
   :version: 1
   :derivation_technique: requirements_based
   :expect: testcase__test_metadata__aaa2: is missing required attribute: `test_type`.

   Has a description so content check passes.


.. testcase:: Missing derivation_technique only
   :id: testcase__test_metadata__aaa3
   :version: 1
   :test_type: feature_integration_test
   :expect: testcase__test_metadata__aaa3: is missing required attribute: `derivation_technique`.

   Has a description so content check passes.


.. testcase:: Has test_type and derivation_technique
   :id: testcase__test_metadata__aaa4
   :version: 1
   :test_type: unit_test
   :derivation_technique: requirements_based
   :expect_not: aaa4

   Has a description too.


.. testcase:: Missing description content
   :id: testcase__test_metadata__bbb1
   :version: 1
   :test_type: unit_test
   :derivation_technique: requirements_based
   :expect: testcase__test_metadata__bbb1: is missing required attribute: `content`.


.. testcase:: FIT linking to comp_req
   :id: testcase__test_metadata__ccc1
   :version: 1
   :test_type: feature_integration_test
   :derivation_technique: requirements_based
   :partially_verifies: comp_req__testcase__abcd
   :expect: Parent need `comp_req__testcase__abcd` does not fulfill condition `id contains feat_req__`.

   Feature Integration Test must link to Feature Requirements.


.. testcase:: CIT linking to feat_req
   :id: testcase__test_metadata__ccc2
   :version: 1
   :test_type: component_integration_test
   :derivation_technique: requirements_based
   :fully_verifies: feat_req__testcase__abcd
   :expect: Parent need `feat_req__testcase__abcd` does not fulfill condition `id contains comp_req__`.

   Component Integration Test must link to Component Requirements.


.. testcase:: UT linking to feat_req
   :id: testcase__test_metadata__ccc3
   :version: 1
   :test_type: unit_test
   :derivation_technique: requirements_based
   :partially_verifies: feat_req__testcase__abcd
   :expect: Parent need `feat_req__testcase__abcd` does not fulfill condition `id contains comp_req__`.

   Unit Test must link to Component Requirements.


.. testcase:: FIT linking to feat_req
   :id: testcase__test_metadata__ccc4
   :version: 1
   :test_type: feature_integration_test
   :derivation_technique: requirements_based
   :partially_verifies: feat_req__testcase__abcd
   :expect_not: ccc4

   Feature Integration Test correctly links to Feature Requirement.


.. testcase:: CIT linking to comp_req
   :id: testcase__test_metadata__ccc5
   :version: 1
   :test_type: component_integration_test
   :derivation_technique: requirements_based
   :fully_verifies: comp_req__testcase__abcd
   :expect_not: ccc5

   Component Integration Test correctly links to Component Requirement.


.. testcase:: UT linking to comp_req
   :id: testcase__test_metadata__ccc6
   :version: 1
   :test_type: unit_test
   :derivation_technique: requirements_based
   :fully_verifies: comp_req__testcase__abcd
   :expect_not: ccc6

   Unit Test correctly links to Component Requirement.


.. testcase:: Unknown test_type
   :id: testcase__test_metadata__ccc7
   :version: 1
   :test_type: some_other_test_type
   :derivation_technique: requirements_based
   :partially_verifies: feat_req__testcase__abcd
   :expect_not: ccc7

   Unrecognized test_type is not subject to link-level checks.

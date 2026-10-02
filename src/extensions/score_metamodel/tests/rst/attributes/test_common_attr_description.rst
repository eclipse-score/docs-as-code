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


.. test_metadata:: Common description attribute
   :id: test_metadata__common_attr_description
   :partially_verifies_list: tool_req__docs_common_attr_description
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks that requirement types accept non-empty descriptions and reject a
   missing description.


.. feat:: Feature target
   :id: feat__description_target
   :version: 1
   :status: valid
   :safety: QM
   :security: NO


.. comp:: Component target
   :id: comp__description_target
   :version: 1
   :status: valid
   :safety: QM
   :security: NO
   :belongs_to: feat__description_target


.. stkh_req:: Requirement used as a tool requirement target
   :id: stkh_req__description__abcd
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: fixture target
   :valid_from: v1.0


.. feat_req:: Feature requirement with a description
   :id: feat_req__description__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__description_target
   :expect_not: is missing required attribute: `content`

   This feature requirement has useful content.


.. feat_req:: Feature requirement without a description
   :id: feat_req__description__aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__description_target
   :expect: is missing required attribute: `content`


.. comp_req:: Component requirement with a description
   :id: comp_req__description__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__description_target
   :expect_not: is missing required attribute: `content`

   This component requirement has useful content.


.. comp_req:: Component requirement without a description
   :id: comp_req__description__aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__description_target
   :expect: is missing required attribute: `content`


.. aou_req:: Assumption with a description
   :id: aou_req__description__aaaa
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :expect_not: is missing required attribute: `content`

   This assumption has useful content.


.. aou_req:: Assumption without a description
   :id: aou_req__description__aaab
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :expect: is missing required attribute: `content`


.. tool_req:: Tool requirement with a description
   :id: tool_req__description_valid
   :version: 1
   :satisfies: stkh_req__description__abcd
   :expect_not: is missing required attribute: `content`

   This tool requirement has useful content.


.. tool_req:: Tool requirement without a description
   :id: tool_req__description_missing
   :version: 1
   :satisfies: stkh_req__description__abcd
   :expect: is missing required attribute: `content`


.. gd_req:: Process requirement with a description
   :id: gd_req__description_with
   :version: 1
   :expect_not: is missing required attribute: `content`

   This process requirement has useful content.


.. gd_req:: Process requirement without a description
   :id: gd_req__description_missing
   :version: 1
   :expect: is missing required attribute: `content`

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
   :id: test_metadata__req_attr_reqtype
   :fully_verifies_list: tool_req__docs_req_attr_reqtype
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that each requirement type except process (gd_req) and tool (tool_req)
   needs carry a `reqtype` attribute with one of the values Functional,
   Interface, Process, or Non-Functional.


.. feat:: Reqtype Test Feature
   :id: feat__reqtype_doc
   :version: 1
   :safety: ASIL_B
   :security: YES
   :status: valid


.. comp:: Reqtype Test Component
   :id: comp__reqtype_doc
   :version: 1
   :safety: ASIL_B
   :security: YES
   :status: valid
   :belongs_to: feat__reqtype_doc


.. stkh_req:: Stakeholder reqtype valid
   :id: stkh_req__options__good
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :rationale: valid reqtype value
   :expect_not: is missing required attribute: `reqtype`, does not follow pattern


.. stkh_req:: Stakeholder reqtype invalid
   :id: stkh_req__options__bad
   :version: 1
   :reqtype: System
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :rationale: invalid reqtype value
   :expect: stkh_req__options__bad.reqtype (System): does not follow pattern


.. stkh_req:: Stakeholder reqtype missing
   :id: stkh_req__options__miss
   :version: 1
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :rationale: missing reqtype value
   :expect: stkh_req__options__miss: is missing required attribute: `reqtype`.


.. feat_req:: Feature reqtype valid
   :id: feat_req__options__good
   :version: 1
   :reqtype: Interface
   :safety: QM
   :security: NO
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__reqtype_doc
   :expect_not: is missing required attribute: `reqtype`, does not follow pattern

   Content of the feature requirement.


.. feat_req:: Feature reqtype invalid
   :id: feat_req__options__bad
   :version: 1
   :reqtype: NonFunctional
   :safety: QM
   :security: NO
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__reqtype_doc
   :expect: feat_req__options__bad.reqtype (NonFunctional): does not follow pattern

   Content of the feature requirement.


.. comp_req:: Component reqtype valid
   :id: comp_req__options__good
   :version: 1
   :reqtype: Process
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__reqtype_doc
   :expect_not: is missing required attribute: `reqtype`, does not follow pattern

   Content of the component requirement.


.. comp_req:: Component reqtype invalid
   :id: comp_req__options__bad
   :version: 1
   :reqtype: functional
   :safety: QM
   :security: NO
   :status: valid
   :satisfied_by: comp__reqtype_doc
   :expect: comp_req__options__bad.reqtype (functional): does not follow pattern

   Content of the component requirement.


.. aou_req:: AoU reqtype valid
   :id: aou_req__options__good
   :version: 1
   :reqtype: Non-Functional
   :safety: QM
   :security: NO
   :status: valid
   :expect_not: is missing required attribute: `reqtype`, does not follow pattern

   Content of the assumption of use requirement.


.. aou_req:: AoU reqtype invalid
   :id: aou_req__options__bad
   :version: 1
   :reqtype: HIGH
   :safety: QM
   :security: NO
   :status: valid
   :expect: aou_req__options__bad.reqtype (HIGH): does not follow pattern

   Content of the assumption of use requirement.


.. tool_req:: Tool reqtype not required
   :id: tool_req__reqtype_ok
   :version: 1
   :satisfies: stkh_req__options__good
   :expect_not: is missing required attribute: `reqtype`

   Tool requirements are exempt from the reqtype classification.


.. gd_req:: Process reqtype not required
   :id: gd_req__reqtype_ok
   :version: 1
   :expect_not: is missing required attribute: `reqtype`

   Process requirements are exempt from the reqtype classification.

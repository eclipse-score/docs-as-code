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
   :id: test_metadata__req_attr_rationale
   :fully_verifies_list: tool_req__docs_req_attr_rationale
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that every stakeholder requirement (stkh_req) contains a `rationale`
   attribute with a non-empty value.


.. stkh_req:: Rationale given
   :id: stkh_req__rationale_doc__good
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :rationale: This requirement is justified by the braking strategy.
   :expect_not: is missing required attribute: `rationale`


.. stkh_req:: Rationale missing
   :id: stkh_req__rationale_doc__miss
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :expect: stkh_req__rationale_doc__miss: is missing required attribute: `rationale`.


.. stkh_req:: Rationale empty
   :id: stkh_req__rationale_doc__empt
   :version: 1
   :reqtype: Functional
   :safety: QM
   :status: valid
   :security: NO
   :valid_from: v1.0
   :rationale:
   :expect: stkh_req__rationale_doc__empt: is missing required attribute: `rationale`.

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
   :id: test_metadata__arch_link_safety_to_req
   :fully_verifies_list: tool_req__docs_arch_link_safety_to_req[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that safety relevant (safety != QM) architecture elements must be
   linked via fulfils to at least one requirement with the exact same
   safety value:
   - a safety relevant element linked to a requirement with the same safety
     value builds without a warning
   - a safety relevant element linked only to a requirement with a
     different safety value triggers the graph check warning
   - a safety relevant element without a fulfils link passes the check
     (at least one linked need fulfills the condition is trivially true,
     link presence stays the job of mandatory links)
   - a non-safety-relevant (QM) element is exempt from the check


.. feat_req:: ASIL_B feature requirement
   :id: feat_req__safety_to_req__asil_req
   :safety: ASIL_B
   :status: valid


.. feat_req:: QM feature requirement
   :id: feat_req__safety_to_req__qm_req
   :safety: QM
   :status: valid


.. Positive: safety relevant element linked to a requirement with the same safety value.

.. logic_arc_int:: ASIL_B interface linked to ASIL_B requirement
   :id: logic_arc_int__safety_to_req__asil_if
   :safety: ASIL_B
   :status: valid
   :fulfils: feat_req__safety_to_req__asil_req
   :expect_not: No linked need in `fulfils` fulfills condition


.. Negative: safety relevant element linked only to a requirement with a different safety value.

.. logic_arc_int:: ASIL_B interface linked to QM requirement
   :id: logic_arc_int__safety_to_req__qm_if
   :safety: ASIL_B
   :status: valid
   :fulfils: feat_req__safety_to_req__qm_req
   :expect: No linked need in `fulfils` fulfills condition `safety == self.safety`


.. No fulfils link: a safety relevant element without fulfils links passes the check.

.. logic_arc_int:: ASIL_B interface without fulfils link
   :id: logic_arc_int__safety_to_req__no_link_if
   :safety: ASIL_B
   :status: valid
   :expect_not: No linked need in `fulfils` fulfills condition


.. Exempt: a QM element is not selected by the check.

.. logic_arc_int:: QM interface linked to QM requirement
   :id: logic_arc_int__safety_to_req__qm_if_exempt
   :safety: QM
   :status: valid
   :fulfils: feat_req__safety_to_req__qm_req
   :expect_not: No linked need in `fulfils` fulfills condition

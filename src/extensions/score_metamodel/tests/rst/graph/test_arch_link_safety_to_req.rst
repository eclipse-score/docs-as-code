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
   :partially_verifies_list: tool_req__docs_arch_link_safety_to_req[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that safety relevant (safety != QM) architecture elements fulfil at
   least one requirement with the same safety level (graph check with
   `check_one`):
   - one of the fulfilled requirements has the same safety level: no warning
   - none of the fulfilled requirements has the same safety level: one warning
     for the link, not one per requirement
   - no fulfils link at all: skipped, the link stays optional
   - comp is not selected: requirements link to it via `satisfied_by`


.. feat_req:: ASIL_B requirement
   :id: feat_req__arch_safety__asil
   :safety: ASIL_B
   :security: NO
   :status: valid

.. feat_req:: QM requirement
   :id: feat_req__arch_safety__qm
   :safety: QM
   :security: NO
   :status: valid

.. feat_req:: Second QM requirement
   :id: feat_req__arch_safety__qm_2
   :safety: QM
   :security: NO
   :status: valid


.. Positive: one of the fulfilled requirements has the same safety level.

.. feat_arc_sta:: Fulfils QM and ASIL_B requirement
   :id: feat_arc_sta__arch_safety__pass
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__arch_safety__qm, feat_req__arch_safety__asil
   :expect_not: No linked need in `fulfils` fulfills


.. Negative: none of the fulfilled requirements has the same safety level.

.. feat_arc_sta:: Fulfils only QM requirements
   :id: feat_arc_sta__arch_safety__fail
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__arch_safety__qm, feat_req__arch_safety__qm_2
   :expect: No linked need in `fulfils` fulfills condition `safety == ASIL_B`
   :expect_not: Parent need `feat_req__arch_safety__qm`


.. Positive: an element without fulfils links is skipped.

.. feat_arc_sta:: Fulfils nothing
   :id: feat_arc_sta__arch_safety__no_links
   :safety: ASIL_B
   :security: NO
   :status: valid
   :expect_not: No linked need in `fulfils` fulfills


.. Exempt: a safety comp satisfying an ASIL_B requirement but fulfilling only a
.. QM AoU is not flagged.

.. aou_req:: QM assumption of use
   :id: aou_req__arch_safety__qm
   :safety: QM
   :security: NO
   :status: valid

.. comp:: Safety component fulfilling only a QM AoU
   :id: comp__arch_safety__exempt
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: aou_req__arch_safety__qm
   :expect_not: No linked need in `fulfils` fulfills

.. comp_req:: ASIL_B requirement satisfied by the safety component
   :id: comp_req__arch_safety__asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :satisfied_by: comp__arch_safety__exempt

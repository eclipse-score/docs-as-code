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
   :id: test_metadata__arch_link_qm_to_safety_req
   :partially_verifies_list: tool_req__docs_arch_link_qm_to_safety_req[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that QM architecture elements are not linked to ASIL requirements:
   - via their own `fulfils` link
   - via the `satisfied_by` link of the requirement (`feat` / `comp`)
   Safety relevant architecture elements are not selected by this check.


.. feat_req:: QM requirement
   :id: feat_req__arch_qm__qm
   :safety: QM
   :security: NO
   :status: valid

.. feat_req:: ASIL_B requirement
   :id: feat_req__arch_qm__asil
   :safety: ASIL_B
   :security: NO
   :status: valid

.. aou_req:: ASIL_B assumption of use
   :id: aou_req__arch_qm__asil
   :safety: ASIL_B
   :security: NO
   :status: valid


.. Positive: QM element fulfils a QM requirement.

.. feat_arc_sta:: QM element fulfils QM requirement
   :id: feat_arc_sta__arch_qm__fulfils_qm
   :safety: QM
   :security: NO
   :status: valid
   :fulfils: feat_req__arch_qm__qm
   :expect_not: does not fulfill condition `safety == QM`


.. Negative: QM element fulfils an ASIL requirement.

.. feat_arc_sta:: QM element fulfils ASIL requirement
   :id: feat_arc_sta__arch_qm__fulfils_asil
   :safety: QM
   :security: NO
   :status: valid
   :fulfils: feat_req__arch_qm__asil
   :expect: Parent need `feat_req__arch_qm__asil` does not fulfill condition `safety == QM`


.. Negative: QM component fulfils an ASIL assumption of use.

.. comp:: QM component fulfils ASIL AoU
   :id: comp__arch_qm__fulfils_asil_aou
   :safety: QM
   :security: NO
   :status: valid
   :fulfils: aou_req__arch_qm__asil
   :expect: Parent need `aou_req__arch_qm__asil` does not fulfill condition `safety == QM`


.. Negative: QM component is satisfying an ASIL requirement (link on the requirement).

.. comp:: QM component satisfies ASIL requirement
   :id: comp__arch_qm__satisfies_asil
   :safety: QM
   :security: NO
   :status: valid
   :expect: Parent need `comp_req__arch_qm__asil` does not fulfill condition `safety == QM`

.. comp_req:: ASIL_B requirement satisfied by QM component
   :id: comp_req__arch_qm__asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :satisfied_by: comp__arch_qm__satisfies_asil


.. Exempt: safety relevant element is not selected.

.. feat_arc_sta:: ASIL element fulfils ASIL requirement
   :id: feat_arc_sta__arch_qm__exempt
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__arch_qm__asil
   :expect_not: does not fulfill condition `safety == QM`

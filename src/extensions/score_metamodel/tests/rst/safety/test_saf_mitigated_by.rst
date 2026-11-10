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
   :id: test_metadata__saf_mitigated_by
   :fully_verifies_list: tool_req__docs_saf_attrs_mitigated_by[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that valid safety analysis needs have at least one ``mitigated_by`` link
   to a requirement with ``safety == ASIL_B``.

   All SAF types are tested:
   * ``feat_saf_dfa``
   * ``comp_saf_dfa``
   * ``feat_saf_fmea``
   * ``comp_saf_fmea``
   * ``plat_saf_dfa``


.. Setup: Architecture stubs (for violates mandatory link)

.. feat_arc_sta:: Stub Feature Static Architecture
   :id: feat_arc_sta__mit__001

.. feat_arc_dyn:: Stub Feature Dynamic Architecture
   :id: feat_arc_dyn__mit__001

.. comp_arc_sta:: Stub Component Static Architecture
   :id: comp_arc_sta__mit__001

.. comp_arc_dyn:: Stub Component Dynamic Architecture
   :id: comp_arc_dyn__mit__001


.. Setup: Requirement stubs for mitigated_by links

.. feat_req:: Feature Requirement ASIL_B
   :id: feat_req__mit__asil_b
   :safety: ASIL_B
   :status: valid

.. feat_req:: Feature Requirement QM
   :id: feat_req__mit__qm
   :safety: QM
   :status: valid

.. comp_req:: Component Requirement ASIL_B
   :id: comp_req__mit__asil_b
   :safety: ASIL_B
   :status: valid

.. comp_req:: Component Requirement QM
   :id: comp_req__mit__qm
   :safety: QM
   :status: valid

.. aou_req:: Assumption of Use Requirement (QM)
   :id: aou_req__mit__qm
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid

.. aou_req:: Assumption of Use Requirement (ASIL_B)
   :id: aou_req__mit__asil_b
   :reqtype: Functional
   :safety: ASIL_B
   :security: NO
   :status: valid

.. stkh_req:: Stakeholder Requirement ASIL_B
   :id: stkh_req__mit__asil_b
   :reqtype: Functional
   :safety: ASIL_B
   :status: valid
   :security: NO
   :rationale: platform safety

.. stkh_req:: Stakeholder Requirement QM
   :id: stkh_req__mit__qm
   :reqtype: Non-Functional
   :safety: QM
   :status: valid
   :security: NO
   :rationale: platform QM


.. Positive Tests: Each SAF type links to ASIL_B requirement or aou_req

.. feat_saf_dfa:: feat DFA mitigated by ASIL_B feat_req
   :id: feat_saf_dfa__mit__pos_01
   :failure_id: df_mit_p01
   :failure_effect: comms loss
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: feat_req__mit__asil_b
   :expect_not: No linked need

.. feat_saf_dfa:: feat DFA mitigated by ASIL_B aou_req
   :id: feat_saf_dfa__mit__pos_02
   :failure_id: df_mit_p02
   :failure_effect: signal lost
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: aou_req__mit__asil_b
   :expect_not: No linked need

.. comp_saf_dfa:: comp DFA mitigated by ASIL_B comp_req
   :id: comp_saf_dfa__mit__pos_01
   :failure_id: df_mit_p03
   :failure_effect: bus timeout
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__mit__001
   :mitigated_by: comp_req__mit__asil_b
   :expect_not: No linked need

.. comp_saf_dfa:: comp DFA mitigated by ASIL_B aou_req
   :id: comp_saf_dfa__mit__pos_02
   :failure_id: df_mit_p04
   :failure_effect: memory corruption
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__mit__001
   :mitigated_by: aou_req__mit__asil_b
   :expect_not: No linked need

.. feat_saf_fmea:: feat FMEA mitigated by ASIL_B feat_req
   :id: feat_saf_fmea__mit__pos_01
   :fault_id: fault_mit_p01
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: feat_req__mit__asil_b
   :expect_not: No linked need

.. feat_saf_fmea:: feat FMEA mitigated by aou_req (ASIL_B)
   :id: feat_saf_fmea__mit__pos_02
   :fault_id: fault_mit_p02
   :failure_effect: sensor drift
   :sufficient: yes
   :status: valid
   :violates: feat_arc_dyn__mit__001
   :mitigated_by: aou_req__mit__asil_b
   :expect_not: No linked need

.. comp_saf_fmea:: comp FMEA mitigated by ASIL_B comp_req
   :id: comp_saf_fmea__mit__pos_01
   :fault_id: fault_mit_p03
   :failure_effect: motor failure
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__mit__001
   :mitigated_by: comp_req__mit__asil_b
   :expect_not: No linked need

.. comp_saf_fmea:: comp FMEA mitigated by ASIL_B aou_req
   :id: comp_saf_fmea__mit__pos_02
   :fault_id: fault_mit_p04
   :failure_effect: encoder fault
   :sufficient: yes
   :status: valid
   :violates: comp_arc_dyn__mit__001
   :mitigated_by: aou_req__mit__asil_b
   :expect_not: No linked need


.. Negative Tests: Missing mitigated_by or only QM requirements

.. feat_saf_dfa:: feat DFA no mitigated_by
   :id: feat_saf_dfa__mit__neg_01
   :failure_id: df_mit_n01
   :failure_effect: missing link
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :expect: No linked need in `mitigated_by`

.. comp_saf_dfa:: comp DFA mitigated_by only QM comp_req
   :id: comp_saf_dfa__mit__neg_02
   :failure_id: df_mit_n02
   :failure_effect: wrong asil
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__mit__001
   :mitigated_by: comp_req__mit__qm
   :expect: No linked need in `mitigated_by` fulfills condition

.. feat_saf_fmea:: feat FMEA no mitigated_by
   :id: feat_saf_fmea__mit__neg_01
   :fault_id: fault_mit_n01
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__mit__001
   :expect: No linked need in `mitigated_by`

.. comp_saf_fmea:: comp FMEA mitigated_by only QM comp_req
   :id: comp_saf_fmea__mit__neg_02
   :fault_id: fault_mit_n02
   :failure_effect: wrong asil
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__mit__001
   :mitigated_by: comp_req__mit__qm
   :expect: No linked need in `mitigated_by` fulfills condition

.. feat_saf_dfa:: feat DFA mitigated_by only QM aou_req
   :id: feat_saf_dfa__mit__neg_03
   :failure_id: df_mit_n03
   :failure_effect: qm aou
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: aou_req__mit__qm
   :expect: No linked need in `mitigated_by` fulfills condition

.. Positive Tests: plat_saf_dfa

.. plat_saf_dfa:: plat DFA mitigated by ASIL_B stkh_req
   :id: plat_saf_dfa__mit__pos_01
   :failure_id: df_mit_p05
   :failure_effect: platform fault
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: stkh_req__mit__asil_b
   :expect_not: No linked need

.. plat_saf_dfa:: plat DFA mitigated by ASIL_B aou_req
   :id: plat_saf_dfa__mit__pos_02
   :failure_id: df_mit_p06
   :failure_effect: platform timeout
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: aou_req__mit__asil_b
   :expect_not: No linked need


.. Negative Tests: plat_saf_dfa

.. plat_saf_dfa:: plat DFA no mitigated_by
   :id: plat_saf_dfa__mit__neg_01
   :failure_id: df_mit_n04
   :failure_effect: no mitigation
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__mit__001
   :expect: No linked need in `mitigated_by`

.. plat_saf_dfa:: plat DFA mitigated_by only QM stkh_req
   :id: plat_saf_dfa__mit__neg_02
   :failure_id: df_mit_n05
   :failure_effect: wrong asil
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__mit__001
   :mitigated_by: stkh_req__mit__qm
   :expect: No linked need in `mitigated_by` fulfills condition


.. Positive Tests: Invalid status SAF needs are not checked

.. feat_saf_dfa:: feat DFA invalid status, no mitigated_by
   :id: feat_saf_dfa__mit__status_invalid
   :failure_id: df_mit_inv
   :failure_effect: ignored
   :sufficient: no
   :status: invalid
   :violates: feat_arc_sta__mit__001
   :expect_not: No linked need

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
   :id: test_metadata__saf_sufficient_check
   :fully_verifies_list: tool_req__docs_saf_attrs_sufficient_check[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that valid safety analysis needs with ``sufficient: yes`` always have
   at least one ``mitigated_by`` entry.

   The check is scoped to ``status == valid``:
   * ``sufficient: yes`` + valid + ``mitigated_by``: no warning
   * ``sufficient: yes`` + valid without ``mitigated_by``: warning
   * ``sufficient: yes`` + draft without ``mitigated_by``: no warning

   All SAF types are tested:
   * ``feat_saf_dfa`` / ``comp_saf_dfa`` / ``plat_saf_dfa``
   * ``feat_saf_fmea`` / ``comp_saf_fmea``


.. Setup: Architecture stubs (for violates mandatory link)

.. feat_arc_sta:: Stub Feature Static Architecture
   :id: feat_arc_sta__suf__001

.. feat_arc_dyn:: Stub Feature Dynamic Architecture
   :id: feat_arc_dyn__suf__001

.. comp_arc_sta:: Stub Component Static Architecture
   :id: comp_arc_sta__suf__001

.. comp_arc_dyn:: Stub Component Dynamic Architecture
   :id: comp_arc_dyn__suf__001


.. Setup: Requirement stubs for mitigated_by links

.. feat_req:: Feature Requirement ASIL_B
   :id: feat_req__suf__asil_b
   :safety: ASIL_B
   :status: valid

.. comp_req:: Component Requirement ASIL_B
   :id: comp_req__suf__asil_b
   :safety: ASIL_B
   :status: valid

.. stkh_req:: Stakeholder Requirement ASIL_B
   :id: stkh_req__suf__asil_b
   :reqtype: Functional
   :safety: ASIL_B
   :status: valid
   :security: NO
   :rationale: platform safety


.. Positive Tests: valid + sufficient: yes + ASIL_B mitigation

.. feat_saf_dfa:: feat DFA sufficient yes mitigated
   :id: feat_saf_dfa__suf__pos_01
   :failure_id: df_suf_p01
   :failure_effect: comms loss
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :mitigated_by: feat_req__suf__asil_b
   :expect_not: No linked need in `mitigated_by`

.. comp_saf_dfa:: comp DFA sufficient yes mitigated
   :id: comp_saf_dfa__suf__pos_01
   :failure_id: df_suf_p02
   :failure_effect: bus timeout
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suf__001
   :mitigated_by: comp_req__suf__asil_b
   :expect_not: No linked need in `mitigated_by`

.. feat_saf_fmea:: feat FMEA sufficient yes mitigated
   :id: feat_saf_fmea__suf__pos_01
   :fault_id: fault_suf_p01
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :mitigated_by: feat_req__suf__asil_b
   :expect_not: No linked need in `mitigated_by`

.. comp_saf_fmea:: comp FMEA sufficient yes mitigated
   :id: comp_saf_fmea__suf__pos_01
   :fault_id: fault_suf_p02
   :failure_effect: motor failure
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suf__001
   :mitigated_by: comp_req__suf__asil_b
   :expect_not: No linked need in `mitigated_by`

.. plat_saf_dfa:: plat DFA sufficient yes mitigated
   :id: plat_saf_dfa__suf__pos_01
   :failure_id: df_suf_p03
   :failure_effect: platform fault
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :mitigated_by: stkh_req__suf__asil_b
   :expect_not: No linked need in `mitigated_by`


.. Negative Tests: valid + sufficient: yes without mitigated_by

.. feat_saf_dfa:: feat DFA sufficient yes no mitigation
   :id: feat_saf_dfa__suf__neg_01
   :failure_id: df_suf_n01
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :expect: No linked need in `mitigated_by`

.. comp_saf_dfa:: comp DFA sufficient yes no mitigation
   :id: comp_saf_dfa__suf__neg_02
   :failure_id: df_suf_n02
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suf__001
   :expect: No linked need in `mitigated_by`

.. feat_saf_fmea:: feat FMEA sufficient yes no mitigation
   :id: feat_saf_fmea__suf__neg_01
   :fault_id: fault_suf_n01
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :expect: No linked need in `mitigated_by`

.. comp_saf_fmea:: comp FMEA sufficient yes no mitigation
   :id: comp_saf_fmea__suf__neg_02
   :fault_id: fault_suf_n02
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suf__001
   :expect: No linked need in `mitigated_by`

.. plat_saf_dfa:: plat DFA sufficient yes no mitigation
   :id: plat_saf_dfa__suf__neg_01
   :failure_id: df_suf_n03
   :failure_effect: missing link
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suf__001
   :expect: No linked need in `mitigated_by`


.. Scoping: draft + sufficient: yes is not checked

.. feat_saf_dfa:: feat DFA draft sufficient yes not checked
   :id: feat_saf_dfa__suf__draft
   :failure_id: df_suf_d01
   :failure_effect: draft only
   :sufficient: yes
   :status: draft
   :violates: feat_arc_sta__suf__001
   :expect_not: No linked need in `mitigated_by`

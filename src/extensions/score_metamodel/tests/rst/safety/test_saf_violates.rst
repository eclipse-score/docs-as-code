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
   :id: test_metadata__saf_violates
   :partially_verifies_list: tool_req__docs_saf_attrs_violates[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that SAF needs link `violates` to correct diagram types per the table:

   * feat_saf_dfa -> feat_arc_sta
   * comp_saf_dfa -> comp_arc_sta
   * feat_saf_fmea -> feat_arc_dyn, feat_arc_sta
   * comp_saf_fmea -> comp_arc_dyn, comp_arc_sta


.. feat_arc_sta:: Stub Feature Static Architecture
   :id: feat_arc_sta__001

.. feat_arc_dyn:: Stub Feature Dynamic Architecture
   :id: feat_arc_dyn__001

.. comp_arc_sta:: Stub Component Static Architecture
   :id: comp_arc_sta__001

.. comp_arc_dyn:: Stub Component Dynamic Architecture
   :id: comp_arc_dyn__001

.. feat_arc_sta:: Stub Feature Static Architecture (bad target)
   :id: feat_arc_sta__bad_001

.. comp_arc_sta:: Stub Component Static Architecture (bad target)
   :id: comp_arc_sta__bad_001

.. comp_arc_dyn:: Stub Component Dynamic Architecture (bad target)
   :id: comp_arc_dyn__bad_001


.. feat_saf_dfa:: feat DFA violates feat arc sta
   :id: feat_saf_dfa__viol__001
   :failure_id: df_001
   :failure_effect: comms loss
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__001


.. comp_saf_dfa:: comp DFA violates comp arc sta
   :id: comp_saf_dfa__viol__001
   :failure_id: df_002
   :failure_effect: signal lost
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__001


.. feat_saf_fmea:: feat FMEA violates feat arc dyn
   :id: feat_saf_fmea__viol__001
   :fault_id: fault_001
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :violates: feat_arc_dyn__001


.. feat_saf_fmea:: feat FMEA violates feat arc sta
   :id: feat_saf_fmea__viol__002
   :fault_id: fault_002
   :failure_effect: sensor drift
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__001


.. comp_saf_fmea:: comp FMEA violates comp arc dyn
   :id: comp_saf_fmea__viol__001
   :fault_id: fault_003
   :failure_effect: motor failure
   :sufficient: yes
   :status: valid
   :violates: comp_arc_dyn__001


.. comp_saf_fmea:: comp FMEA violates comp arc sta
   :id: comp_saf_fmea__viol__002
   :fault_id: fault_004
   :failure_effect: encoder fault
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__001


.. feat_saf_dfa:: feat DFA violates comp arc sta
   :id: feat_saf_dfa__viol__bad_001
   :failure_id: df_bad_001
   :failure_effect: wrong link
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__bad_001
   :expect: must reference Feature & Feature Package Diagram


.. feat_saf_fmea:: feat FMEA violates comp arc
   :id: feat_saf_fmea__viol__bad_001
   :fault_id: fault_bad_001
   :failure_effect: wrong link target
   :sufficient: yes
   :status: valid
   :violates: comp_arc_dyn__bad_001
   :expect: must reference Feature Sequence Diagram


.. comp_saf_dfa:: comp DFA violates feat arc
   :id: comp_saf_dfa__viol__bad_001
   :failure_id: df_bad_002
   :failure_effect: wrong link target
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__bad_001
   :expect: must reference Component Package Diagram

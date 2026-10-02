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
   :id: test_metadata__saf_attrs_sufficient_check
   :fully_verifies_list: tool_req__docs_saf_attrs_sufficient_check[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that safety analysis needs which rate their mitigation as sufficient
   (sufficient == yes) are required to link at least one mitigation via
   mitigated_by.  Each of the five safety analysis types is checked with:
   - sufficient == yes plus a mitigated_by entry, expecting no warning
   - sufficient == yes without a mitigated_by entry, expecting a warning
   - sufficient == no without a mitigated_by entry, expecting no warning


.. Setup link targets, intentionally minimal (not asserted against).

.. feat_arc_sta:: Stub Feature Static Architecture
   :id: feat_arc_sta__suff__001

.. feat_arc_dyn:: Stub Feature Dynamic Architecture
   :id: feat_arc_dyn__suff__001

.. comp_arc_sta:: Stub Component Static Architecture
   :id: comp_arc_sta__suff__001

.. comp_arc_dyn:: Stub Component Dynamic Architecture
   :id: comp_arc_dyn__suff__001

.. aou_req:: Stub Assumption of Use Requirement
   :id: aou_req__suff__001


.. plat_saf_dfa:: Sufficient with mitigation
   :id: plat_saf_dfa__test__sc_ok_001
   :version: 1
   :failure_id: df_sc_ok_001
   :failure_effect: comms loss
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :mitigated_by: aou_req__suff__001
   :expect_not: requires at least one `mitigated_by`

   Platform DFA rated sufficient with a linked mitigation.


.. plat_saf_dfa:: Sufficient without mitigation
   :id: plat_saf_dfa__test__sc_missing_001
   :version: 1
   :failure_id: df_sc_missing_001
   :failure_effect: comms loss
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect: requires at least one `mitigated_by`

   Platform DFA rated sufficient without a linked mitigation.


.. plat_saf_dfa:: Not sufficient without mitigation
   :id: plat_saf_dfa__test__sc_no_001
   :version: 1
   :failure_id: df_sc_no_001
   :failure_effect: comms loss
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect_not: requires at least one `mitigated_by`

   Platform DFA rated not sufficient and without a mitigated_by entry is fine.


.. feat_saf_dfa:: Sufficient with mitigation
   :id: feat_saf_dfa__test__sc_ok_001
   :version: 1
   :failure_id: df_sc_ok_002
   :failure_effect: signal lost
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :mitigated_by: aou_req__suff__001
   :expect_not: requires at least one `mitigated_by`

   Feature DFA rated sufficient with a linked mitigation.


.. feat_saf_dfa:: Sufficient without mitigation
   :id: feat_saf_dfa__test__sc_missing_001
   :version: 1
   :failure_id: df_sc_missing_002
   :failure_effect: signal lost
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect: requires at least one `mitigated_by`

   Feature DFA rated sufficient without a linked mitigation.


.. feat_saf_dfa:: Not sufficient without mitigation
   :id: feat_saf_dfa__test__sc_no_001
   :version: 1
   :failure_id: df_sc_no_002
   :failure_effect: signal lost
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect_not: requires at least one `mitigated_by`

   Feature DFA rated not sufficient and without a mitigated_by entry is fine.


.. comp_saf_dfa:: Sufficient with mitigation
   :id: comp_saf_dfa__test__sc_ok_001
   :version: 1
   :failure_id: df_sc_ok_003
   :failure_effect: power failure
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suff__001
   :mitigated_by: aou_req__suff__001
   :expect_not: requires at least one `mitigated_by`

   Component DFA rated sufficient with a linked mitigation.


.. comp_saf_dfa:: Sufficient without mitigation
   :id: comp_saf_dfa__test__sc_missing_001
   :version: 1
   :failure_id: df_sc_missing_003
   :failure_effect: power failure
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suff__001
   :expect: requires at least one `mitigated_by`

   Component DFA rated sufficient without a linked mitigation.


.. comp_saf_dfa:: Not sufficient without mitigation
   :id: comp_saf_dfa__test__sc_no_001
   :version: 1
   :failure_id: df_sc_no_003
   :failure_effect: power failure
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__suff__001
   :expect_not: requires at least one `mitigated_by`

   Component DFA rated not sufficient and without a mitigated_by entry is fine.


.. feat_saf_fmea:: Sufficient with mitigation
   :id: feat_saf_fmea__test__sc_ok_001
   :version: 1
   :fault_id: fault_sc_ok_001
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :mitigated_by: aou_req__suff__001
   :expect_not: requires at least one `mitigated_by`

   Feature FMEA rated sufficient with a linked mitigation.


.. feat_saf_fmea:: Sufficient without mitigation
   :id: feat_saf_fmea__test__sc_missing_001
   :version: 1
   :fault_id: fault_sc_missing_001
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect: requires at least one `mitigated_by`

   Feature FMEA rated sufficient without a linked mitigation.


.. feat_saf_fmea:: Not sufficient without mitigation
   :id: feat_saf_fmea__test__sc_no_001
   :version: 1
   :fault_id: fault_sc_no_001
   :failure_effect: valve stuck
   :sufficient: no
   :status: valid
   :violates: feat_arc_sta__suff__001
   :expect_not: requires at least one `mitigated_by`

   Feature FMEA rated not sufficient and without a mitigated_by entry is fine.


.. comp_saf_fmea:: Sufficient with mitigation
   :id: comp_saf_fmea__test__sc_ok_001
   :version: 1
   :fault_id: fault_sc_ok_002
   :failure_effect: software crash
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suff__001
   :mitigated_by: aou_req__suff__001
   :expect_not: requires at least one `mitigated_by`

   Component FMEA rated sufficient with a linked mitigation.


.. comp_saf_fmea:: Sufficient without mitigation
   :id: comp_saf_fmea__test__sc_missing_001
   :version: 1
   :fault_id: fault_sc_missing_002
   :failure_effect: software crash
   :sufficient: yes
   :status: valid
   :violates: comp_arc_sta__suff__001
   :expect: requires at least one `mitigated_by`

   Component FMEA rated sufficient without a linked mitigation.


.. comp_saf_fmea:: Not sufficient without mitigation
   :id: comp_saf_fmea__test__sc_no_001
   :version: 1
   :fault_id: fault_sc_no_002
   :failure_effect: software crash
   :sufficient: no
   :status: valid
   :violates: comp_arc_sta__suff__001
   :expect_not: requires at least one `mitigated_by`

   Component FMEA rated not sufficient and without a mitigated_by entry is fine.

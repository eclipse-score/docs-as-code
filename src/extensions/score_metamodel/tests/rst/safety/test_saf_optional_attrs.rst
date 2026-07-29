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
   :id: test_metadata__saf_optional_attrs
   :fully_verifies_list: tool_req__docs_saf_attrs_mitigation_issue[version==1], tool_req__docs_saf_attrs_safety_relevant[version==1], tool_req__docs_saf_attrs_root_cause[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests optional attributes for safety analysis types:
   - mitigation_issue: GitHub issue URL pattern
   - safety_relevant: yes/no for all SAF types
   - root_cause: non-empty content for FMEA


.. feat_saf_dfa:: Valid mitigation issue
   :id: feat_saf_dfa__opt__001
   :version: 1
   :failure_id: df_opt_001
   :failure_effect: comms loss
   :sufficient: no
   :status: valid
   :mitigation_issue: https://github.com/eclipse-score/docs-as-code/issues/42
   :expect_not: need_id


.. feat_saf_fmea:: Valid mitigation issue 2
   :id: feat_saf_fmea__opt__001
   :version: 1
   :fault_id: fault_opt_001
   :failure_effect: valve stuck
   :sufficient: yes
   :status: valid
   :mitigation_issue: https://github.com/owner/repo/issues/123
   :expect_not: need_id


.. comp_saf_dfa:: Safety relevant yes
   :id: comp_saf_dfa__opt__001
   :version: 1
   :failure_id: df_opt_003
   :failure_effect: signal noise
   :sufficient: no
   :status: valid
   :safety_relevant: yes
   :expect_not: need_id


.. comp_saf_dfa:: Safety relevant no
   :id: comp_saf_dfa__opt__002
   :version: 1
   :failure_id: df_opt_004
   :failure_effect: power failure
   :sufficient: yes
   :status: valid
   :safety_relevant: no
   :expect_not: need_id


.. feat_saf_dfa:: Invalid safety relevant
   :id: feat_saf_dfa__opt__bad_001
   :version: 1
   :failure_id: df_opt_bad_001
   :failure_effect: bad value
   :sufficient: no
   :status: valid
   :safety_relevant: perhaps
   :expect: does not follow pattern


.. feat_saf_fmea:: FMEA with root cause
   :id: feat_saf_fmea__opt__002
   :version: 1
   :fault_id: fault_opt_002
   :failure_effect: component failure
   :sufficient: no
   :status: valid
   :root_cause: manufacturing defect in solder joints
   :expect_not: need_id


.. comp_saf_fmea:: Comp FMEA with root cause
   :id: comp_saf_fmea__opt__001
   :version: 1
   :fault_id: fault_opt_003
   :failure_effect: software crash
   :sufficient: yes
   :status: valid
   :root_cause: null pointer dereference in interrupt handler
   :expect_not: need_id

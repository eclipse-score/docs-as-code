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
   :id: test_metadata__saf_types
   :fully_verifies_list: tool_req__docs_saf_types[version==2]
   :partially_verifies_list: tool_req__docs_saf_attrs_mandatory[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that all safety analysis need types are supported and that
   mandatory attributes are enforced.


.. feat_saf_fmea:: Feature FMEA entry
   :id: feat_saf_fmea__test__001
   :status: valid
   :fault_id: fault_1
   :failure_effect: system hangs
   :sufficient: yes
   :expect_not: unknown directive


.. comp_saf_fmea:: Component FMEA entry
   :id: comp_saf_fmea__test__001
   :status: valid
   :fault_id: fault_2
   :failure_effect: valve stuck open
   :sufficient: no
   :expect_not: unknown directive


.. plat_saf_dfa:: Platform DFA entry
   :id: plat_saf_dfa__test__001
   :status: valid
   :failure_id: df_1
   :failure_effect: signal delay
   :sufficient: yes
   :expect_not: unknown directive


.. feat_saf_dfa:: Feature DFA entry
   :id: feat_saf_dfa__test__001
   :status: valid
   :failure_id: df_2
   :failure_effect: unexpected output
   :sufficient: yes
   :expect_not: unknown directive


.. comp_saf_dfa:: Component DFA entry
   :id: comp_saf_dfa__test__001
   :status: valid
   :failure_id: df_3
   :failure_effect: communication loss
   :sufficient: no
   :expect_not: unknown directive


.. feat_saf_fmea:: Missing failure effect
   :id: feat_saf_fmea__test__bad_001
   :status: valid
   :fault_id: fault_bad
   :sufficient: yes
   :expect: is missing required attribute: `failure_effect`.


.. comp_saf_dfa:: Missing status
   :id: comp_saf_dfa__test__bad_001
   :failure_id: df_bad
   :failure_effect: no status
   :sufficient: yes
   :expect: is missing required attribute: `status`.

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
   :id: test_metadata__saf_mandatory_attrs
   :fully_verifies_list:
     tool_req__docs_saf_attr_dfa_failure_id[version==2],
     tool_req__docs_saf_attr_fmea_fault_id[version==2],
     tool_req__docs_saf_attrs_sufficient[version==1],
     tool_req__docs_saf_attrs_content[version==2]
   :partially_verifies_list: tool_req__docs_saf_attrs_mandatory[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that all safety analysis types have required mandatory attributes:
   - DFA: failure_id
   - FMEA: fault_id
   - All: failure_effect, status, sufficient, content


.. feat_saf_dfa:: Missing failure_id
   :id: feat_saf_dfa__test__missing_fid
   :version: 1
   :status: valid
   :failure_effect: signal lost
   :sufficient: yes
   :expect: is missing required attribute: `failure_id`


.. comp_saf_dfa:: Valid failure_id
   :id: comp_saf_dfa__test__good_fid
   :version: 1
   :status: valid
   :failure_id: df_good_001
   :failure_effect: communication lost
   :sufficient: no
   :expect_not: missing required attribute: `failure_id`


.. feat_saf_fmea:: Missing fault_id
   :id: feat_saf_fmea__test__missing_fault
   :version: 1
   :status: valid
   :failure_effect: valve stuck
   :sufficient: yes
   :expect: is missing required attribute: `fault_id`


.. comp_saf_fmea:: Valid fault_id
   :id: comp_saf_fmea__test__good_fault
   :version: 1
   :status: valid
   :fault_id: fault_good_001
   :failure_effect: valve stuck
   :sufficient: no
   :expect_not: missing required attribute: `fault_id`


.. plat_saf_dfa:: Missing failure_effect
   :id: plat_saf_dfa__test__missing_fe
   :version: 1
   :status: valid
   :failure_id: df_fe_bad
   :sufficient: yes
   :expect: is missing required attribute: `failure_effect`


.. feat_saf_dfa:: Missing sufficient
   :id: feat_saf_dfa__test__missing_suff
   :version: 1
   :status: valid
   :failure_id: df_suff_bad
   :failure_effect: output wrong
   :expect: is missing required attribute: `sufficient`


.. feat_saf_fmea:: Valid sufficient yes
   :id: feat_saf_fmea__test__suff_ok_1
   :version: 1
   :status: valid
   :fault_id: fault_suff_ok_1
   :failure_effect: system error
   :sufficient: yes
   :expect_not: does not follow pattern


.. comp_saf_dfa:: Valid sufficient no
   :id: comp_saf_dfa__test__suff_ok_2
   :version: 1
   :status: valid
   :failure_id: df_suff_ok_2
   :failure_effect: signal lost
   :sufficient: no
   :expect_not: does not follow pattern


.. feat_saf_dfa:: Invalid sufficient value
   :id: feat_saf_dfa__test__suff_bad
   :version: 1
   :status: valid
   :failure_id: df_suff_bad_2
   :failure_effect: bad output
   :sufficient: maybe
   :expect: does not follow pattern


.. feat_saf_fmea:: Valid content
   :id: feat_saf_fmea__test__content_ok
   :version: 1
   :status: valid
   :fault_id: fault_content_ok
   :failure_effect: crash
   :sufficient: yes
   :expect_not: is missing required attribute: `content`.

   This is the content of the FMEA entry.


.. comp_saf_dfa:: Missing content
   :id: comp_saf_dfa__test__content_bad
   :version: 1
   :status: valid
   :failure_id: df_content_bad
   :failure_effect: no response
   :sufficient: no
   :expect: is missing required attribute: `content`.

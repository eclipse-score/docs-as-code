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
   :id: test_metadata__sec_types
   :fully_verifies_list: tool_req__docs_sec_types[version==2], tool_req__docs_sec_attrs_mandatory[version==1]
   :partially_verifies_list: tool_req__docs_sec_attrs_optional[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that security analysis types are supported with mandatory and optional attributes.


.. feat_sec_threat:: STRIDE threat feature
   :id: feat_sec_threat__test__001
   :version: 1
   :threat_id: EX_01_01
   :status: valid
   :expect_not: need_id

   Feature STRIDE threat analysis entry.


.. comp_sec_threat:: STRIDE threat component
   :id: comp_sec_threat__test__001
   :version: 1
   :threat_id: MT_01_01
   :status: valid
   :expect_not: need_id

   Component STRIDE threat analysis entry.


.. plat_sec_threat:: STRIDE threat platform
   :id: plat_sec_threat__test__001
   :version: 1
   :threat_id: AU_01_01
   :status: valid
   :expect_not: need_id

   Platform STRIDE threat analysis entry.


.. feat_sec_ana:: Threat scenario feature
   :id: feat_sec_ana__test__001
   :version: 1
   :threat_scenario_id: AS_01_01
   :status: valid
   :sufficient: no
   :threat_effect: unauthorized access
   :expect_not: need_id

   Feature threat scenario analysis.


.. comp_sec_ana:: Threat scenario component
   :id: comp_sec_ana__test__001
   :version: 1
   :threat_scenario_id: CO_01_01
   :status: valid
   :sufficient: yes
   :threat_effect: denial of service
   :expect_not: need_id

   Component threat scenario analysis.


.. plat_sec_ana:: Threat scenario platform
   :id: plat_sec_ana__test__001
   :version: 1
   :threat_scenario_id: SC_01_02
   :status: valid
   :sufficient: no
   :threat_effect: information disclosure
   :expect_not: need_id

   Platform threat scenario analysis.


.. feat_sec_ana:: Missing threat effect
   :id: feat_sec_ana__test__missing_effect
   :version: 1
   :threat_scenario_id: AS_01_02
   :status: valid
   :sufficient: yes
   :expect: is missing required attribute: `threat_effect`

   Failing threat scenario without threat_effect.


.. comp_sec_ana:: Missing sufficient
   :id: comp_sec_ana__test__missing_sufficient
   :version: 1
   :threat_scenario_id: CO_01_02
   :status: valid
   :threat_effect: crash
   :expect: is missing required attribute: `sufficient`

   Failing threat scenario without sufficient.


.. feat_sec_ana:: Invalid sufficient
   :id: feat_sec_ana__test__bad_sufficient
   :version: 1
   :threat_scenario_id: AS_01_04
   :status: valid
   :sufficient: maybe
   :threat_effect: failure
   :expect: does not follow pattern

   Failing threat scenario with invalid sufficient value.


.. feat_sec_ana:: With mitigation issue
   :id: feat_sec_ana__test__mitigation
   :version: 1
   :threat_scenario_id: SI_01_02
   :status: valid
   :sufficient: no
   :threat_effect: data leak
   :mitigation_issue: https://github.com/eclipse-score/docs-as-code/issues/42
   :expect_not: need_id

   Threat scenario with mitigation tracking.


.. comp_sec_ana:: Invalid mitigation issue URL
   :id: comp_sec_ana__test__bad_mitigation
   :version: 1
   :threat_scenario_id: UI_01_01
   :status: valid
   :sufficient: yes
   :threat_effect: spoofing
   :mitigation_issue: not-a-valid-url
   :expect: does not follow pattern

   Failing threat scenario with invalid mitigation issue URL.

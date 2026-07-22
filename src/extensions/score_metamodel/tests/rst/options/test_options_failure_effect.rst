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
   :id: test_metadata__failure_effect
   :partially_verifies_list: tool_req__docs_saf_attr_fmea_failure_effect
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that every Safety Analysis (FMEA and DFA) has a mandatory,
   non-empty `failure_effect` attribute.


.. Negative: `feat_saf_fmea` without `failure_effect` — warning expected.

.. feat_saf_fmea:: Missing failure_effect
   :id: feat_saf_fmea__test__no_failure_effect
   :fault_id: FMEA_01
   :sufficient: yes
   :status: valid
   :expect: feat_saf_fmea__test__no_failure_effect: is missing required attribute: `failure_effect`.

   Some content.


.. Positive: `feat_saf_fmea` with `failure_effect` — no warning expected.

.. feat_saf_fmea:: With failure_effect
   :id: feat_saf_fmea__test__with_fe
   :fault_id: FMEA_02
   :failure_effect: Unintended actuation of the analysed element
   :sufficient: yes
   :status: valid
   :version: 1
   :expect_not: required attribute: `failure_effect`

   Some content.


.. Negative: `comp_saf_fmea` without `failure_effect` — warning expected.

.. comp_saf_fmea:: Missing failure_effect
   :id: comp_saf_fmea__test__no_failure_effect
   :fault_id: FMEA_03
   :sufficient: yes
   :status: valid
   :expect: comp_saf_fmea__test__no_failure_effect: is missing required attribute: `failure_effect`.

   Some content.


.. Positive: `comp_saf_fmea` with `failure_effect` — no warning expected.

.. comp_saf_fmea:: With failure_effect
   :id: comp_saf_fmea__test__with_fe
   :fault_id: FMEA_04
   :failure_effect: Unintended actuation of the analysed element
   :sufficient: yes
   :status: valid
   :version: 1
   :expect_not: required attribute: `failure_effect`

   Some content.


.. Negative: `feat_saf_dfa` without `failure_effect` — warning expected.

.. feat_saf_dfa:: Missing failure_effect
   :id: feat_saf_dfa__test__no_failure_effect
   :failure_id: DFA_01
   :sufficient: yes
   :status: valid
   :expect: feat_saf_dfa__test__no_failure_effect: is missing required attribute: `failure_effect`.

   Some content.


.. Positive: `feat_saf_dfa` with `failure_effect` — no warning expected.

.. feat_saf_dfa:: With failure_effect
   :id: feat_saf_dfa__test__with_fe
   :failure_id: DFA_02
   :failure_effect: Unintended actuation of the analysed element
   :sufficient: yes
   :status: valid
   :version: 1
   :expect_not: required attribute: `failure_effect`

   Some content.


.. Negative: `comp_saf_dfa` without `failure_effect` — warning expected.

.. comp_saf_dfa:: Missing failure_effect
   :id: comp_saf_dfa__test__no_failure_effect
   :failure_id: DFA_03
   :sufficient: yes
   :status: valid
   :expect: comp_saf_dfa__test__no_failure_effect: is missing required attribute: `failure_effect`.

   Some content.


.. Positive: `comp_saf_dfa` with `failure_effect` — no warning expected.

.. comp_saf_dfa:: With failure_effect
   :id: comp_saf_dfa__test__with_fe
   :failure_id: DFA_04
   :failure_effect: Unintended actuation of the analysed element
   :sufficient: yes
   :status: valid
   :version: 1
   :expect_not: required attribute: `failure_effect`

   Some content.


.. Negative: `plat_saf_dfa` without `failure_effect` — warning expected.

.. plat_saf_dfa:: Missing failure_effect
   :id: plat_saf_dfa__test__no_failure_effect
   :failure_id: DFA_05
   :sufficient: yes
   :status: valid
   :expect: plat_saf_dfa__test__no_failure_effect: is missing required attribute: `failure_effect`.

   Some content.


.. Positive: `plat_saf_dfa` with `failure_effect` — no warning expected.

.. plat_saf_dfa:: With failure_effect
   :id: plat_saf_dfa__test__with_fe
   :failure_id: DFA_06
   :failure_effect: Unintended actuation of the analysed element
   :sufficient: yes
   :status: valid
   :version: 1
   :expect_not: required attribute: `failure_effect`

   Some content.


.. Negative: `failure_effect` is empty string — warning expected.

.. feat_saf_fmea:: Empty failure_effect
   :id: feat_saf_fmea__test__empty_failure_effect
   :fault_id: FMEA_05
   :failure_effect: 
   :sufficient: yes
   :status: valid
   :expect: feat_saf_fmea__test__empty_failure_effect: is missing required attribute: `failure_effect`.

   Some content.

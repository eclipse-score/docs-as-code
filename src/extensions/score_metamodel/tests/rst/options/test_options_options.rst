..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
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
#CHECK: check_options

.. Required option: `status` is missing
#EXPECT: std_wp__test__abcd: is missing required option: `status`.

.. std_wp:: This is a test
   :id: std_wp__test__abcd

.. All required options are present
#EXPECT-NOT: is missing required option

.. std_wp:: This is a test
   :id: std_wp__test__abce
   :status: active

.. Required link `satisfies` refers to wrong requirement type
#EXPECT: feat_req__abce.satisfies (['std_wp__test__abce']): does not follow pattern `^stkh_req__.*$`.

.. feat_req:: Child requirement
   :id: feat_req__abce
   :satisfies: std_wp__test__abce

.. Optional link `supported_by` refers to wrong requirement type
   This check is disabled in check_options.py:114
   #EXPECT: wf__abcd.supported_by (['feat_req__abce']): does not follow pattern `^rl__.*$`.

   .. std_wp:: This is a test
      :id: wf__abcd
      :supported_by: feat_req__abce

.. Optional link `supported_by` refers to the correct requirement type
   This check is disabled in check_options.py:114
   #EXPECT-NOT: does not follow pattern `^rl__.*$`.

   .. std_wp:: This is a test
      :id: wf__abcd
      :supported_by: rl__abcd

   .. rl:: This is a test
      :id: rl__abcd

   .. Required link: `satisfies` is missing
   #EXPECT: feat_req__abcf: is missing required link: `satisfies`.

   .. feat_req:: Child requirement
      :id: feat_req__abcf

.. All required links are present
#EXPECT-NOT: feat_req__abcg: is missing required link

.. feat_req:: Child requirement
   :id: feat_req__abcg
   :satisfies: stkh_req__abcd

.. stkh_req:: Parent requirement
   :id: stkh_req__abcd

.. List of elements which an attribute safety. Preparation of a test that actually could be need to ensure that ASIL_D is not used.
.. doc__
.. stkh_req__
.. feat_req__
.. comp_req__
.. tool_req__
.. aou_req__
.. feat_arc_sta__
.. feat_arc_dyn__
.. logic_arc_int__
.. logic_arc_int_op__
.. comp_arc_sta__
.. comp_arc_dyn__
.. real_arc_int__
.. real_arc_int_op__
.. dd_sta__
.. dd_dyn__
.. sw_unit__


.. Test if the `sufficient` option for Safety Analysis (FMEA and DFA) follows the pattern `^(yes|no)$`
#EXPECT: feat_saf_fmea__test__bad_1.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__bad_1
   :sufficient: QM

#EXPECT-NOT: feat_saf_fmea__test__good_2.sufficient (yes): does not follow pattern `^(yes|no)$`.

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__2
   :sufficient: yes

#EXPECT-NOT: feat_saf_fmea__test__good_3.sufficient (no): does not follow pattern `^(yes|no)$`.

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__3
   :sufficient: no

#EXPECT: comp_saf_fmea__test__bad_4.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__bad_4
   :sufficient: QM

#EXPECT-NOT: comp_saf_fmea__test__good_5.sufficient (yes): does not follow pattern `^(yes|no)$`.

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__5
   :sufficient: yes

#EXPECT-NOT: comp_saf_fmea__test__good_6.sufficient (no): does not follow pattern `^(yes|no)$`.

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__6
   :sufficient: no

#EXPECT: feat_plat_saf_dfa__test__bad_7.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_plat_saf_dfa:: This is a test
   :id: feat_plat_saf_dfa__test__bad_7
   :sufficient: QM

#EXPECT-NOT: feat_plat_saf_dfa__test__good_8.sufficient (yes): does not follow pattern `^(yes|no)$`.

.. feat_plat_saf_dfa:: This is a test
   :id: feat_plat_saf_dfa__test__8
   :sufficient: yes

#EXPECT-NOT: feat_plat_saf_dfa__test__good_9.sufficient (no): does not follow pattern `^(yes|no)$`.

.. feat_plat_saf_dfa:: This is a test
   :id: feat_plat_saf_dfa__test__9
   :sufficient: no

#EXPECT: feat_saf_dfa__test__bad_10.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__bad_10
   :sufficient: QM

#EXPECT-NOT: feat_saf_dfa__test__good_11.sufficient (yes): does not follow pattern `^(yes|no)$`.

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__11
   :sufficient: yes

#EXPECT-NOT: feat_saf_dfa__test__good_12.sufficient (no): does not follow pattern `^(yes|no)$`.

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__12
   :sufficient: no

#EXPECT: comp_saf_dfa__test__bad_13.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test__bad_13
   :sufficient: QM

#EXPECT-NOT: comp_saf_dfa__test__good_14.sufficient (yes): does not follow pattern `^(yes|no)$`.

.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test__14
   :sufficient: yes

#EXPECT-NOT: comp_saf_dfa__test__good_15.sufficient (no): does not follow pattern `^(yes|no)$`.

.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test__15
   :sufficient: no

.. Test that the `sufficient` option is case sensitive and does not accept values other than `yes` or `no`
#EXPECT: feat_saf_fmea__test__bad_16.sufficient (yEs): does not follow pattern `^(yes|no)$`.

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__bad_16
   :sufficient: yEs



.. comp_req:: Child requirement ASIL_B
   :id: comp_req__child__ASIL_B
   :safety: ASIL_B
   :status: valid


.. Negative Test: Linked to a non-allowed requirement type.
#EXPECT: feat_saf_fmea__child__25.mitigates (['comp_req__child__ASIL_B']): does not follow pattern `^(feat_req__.*|aou_req__.*)$`.

.. feat_saf_fmea:: Child requirement 25
   :id: feat_saf_fmea__child__25
   :safety: ASIL_B
   :status: valid
   :mitigates: comp_req__child__ASIL_B

.. Negative Test: Linked to a non-allowed requirement type.
#EXPECT: feat_saf_fmea__child__26.verifies (['comp_req__child__ASIL_B']): does not follow pattern `^feat_arc_dyn__[0-9a-z_]*$`.

.. feat_saf_fmea:: Child requirement 26
   :id: feat_saf_fmea__child__26
   :safety: ASIL_B
   :status: valid
   :verifies: comp_req__child__ASIL_B

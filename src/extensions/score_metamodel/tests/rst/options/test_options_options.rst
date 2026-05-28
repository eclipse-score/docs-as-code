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


..
   Required option: `status` is missing
#EXPECT: std_wp__test__abcd: is missing required attribute: `status`.

.. std_wp:: This is a test
   :id: std_wp__test__abcd



.. All required options are present
#EXPECT-NOT: attribute

.. std_wp:: This is a test
   :id: std_wp__test__abce
   :status: active



.. Required link `satisfies` refers to wrong requirement type
#EXPECT: feat_req__abce: references 'std_wp__test__abce' as 'satisfies', but it must reference Stakeholder Requirement (stkh_req).

.. feat_req:: Child requirement
   :id: feat_req__abce
   :satisfies: std_wp__test__abce



.. All required links are present
#EXPECT-NOT: feat_req__abcg: is missing required link

.. feat_req:: Child requirement
   :id: feat_req__abcg
   :satisfies: stkh_req__abcd

.. stkh_req:: Parent requirement
   :id: stkh_req__abcd



.. Test if the `sufficient` option for Safety Analysis (FMEA and DFA) follows the pattern `^(yes|no)$`
#EXPECT: feat_saf_fmea__test__bad_1.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__bad_1
   :sufficient: QM


#EXPECT-NOT: pattern

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__2
   :sufficient: yes


#EXPECT-NOT: pattern

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test__3
   :sufficient: no


#EXPECT: comp_saf_fmea__test__bad_4.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__bad_4
   :sufficient: QM


#EXPECT-NOT: pattern

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__5
   :sufficient: yes


#EXPECT-NOT: pattern

.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test__6
   :sufficient: no


#EXPECT: feat_saf_dfa__test__bad_7.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__bad_7
   :sufficient: QM


#EXPECT-NOT: pattern

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__8
   :sufficient: yes


#EXPECT-NOT: pattern

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__9
   :sufficient: no


#EXPECT: feat_saf_dfa__test__bad_10.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__bad_10
   :sufficient: QM


#EXPECT-NOT: pattern

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__11
   :sufficient: yes


#EXPECT-NOT: pattern

.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test__12
   :sufficient: no


#EXPECT: comp_saf_dfa__test__bad_13.sufficient (QM): does not follow pattern `^(yes|no)$`.

.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test__bad_13
   :sufficient: QM


#EXPECT-NOT: pattern

.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test__14
   :sufficient: yes


#EXPECT-NOT: pattern

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



..
   This Test can not be tested at the moment without enabeling that optional checks are also linked.
   TODO: Re-enable this check
.. Negative Test: Linked to a non-allowed requirement type.
.. #EXPECT: feat_saf_fmea__child__25.mitigated_by (['comp_req__child__ASIL_B']): does not follow pattern `^(feat_req__.*|aou_req__.*)$`.
..
.. .. feat_saf_fmea:: Child requirement 25
..    :id: feat_saf_fmea__child__25
..    :safety: ASIL_B
..    :status: valid
..    :mitigated_by: comp_req__child__ASIL_B



--- feat_saf_fmea violates begin ---

.. Negative Test: Linked to a non-allowed requirement type.
#EXPECT: feat_saf_fmea__child__26: references 'comp_req__child__ASIL_B' as 'violates', but it must reference Feature Sequence Diagram (feat_arc_dyn) or Feature & Feature Package Diagram (feat_arc_sta).

.. feat_saf_fmea:: Child requirement 26
   :id: feat_saf_fmea__child__26
   :violates: comp_req__child__ASIL_B

.. feat_saf_fmea can link either feat_arc_dyn or feat_arc_sta

Expect no errors related to "violates" field. We need to be generic for expect-not verifications.
#EXPECT-NOT: violates

.. feat_saf_fmea:: This requirement links a feat_arc_dyn
   :id: feat_saf_fmea__violate__dyn
   :violates: feat_arc_dyn__test_good_1


Expect no errors related to "violates" field. We need to be generic for expect-not verifications.
#EXPECT-NOT: violates

.. feat_saf_fmea:: This requirement links a feat_arc_sta
   :id: feat_saf_fmea__violate__sta
   :violates: feat_arc_sta__test_good_1

--- feat_saf_fmea violates end ---


.. Tests if the attribute `safety` follows the pattern `^(QM|ASIL_B)$`
#EXPECT-NOT: pattern

.. document:: This is a test document
   :id: doc__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. document:: This is a test document
   :id: doc__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. stkh_req:: This is a test
   :id: stkh_req__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. stkh_req:: This is a test
   :id: stkh_req__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. feat_req:: This is a test
   :id: feat_req__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. feat_req:: This is a test
   :id: feat_req__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. comp_req:: This is a test
   :id: comp_req__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. comp_req:: This is a test
   :id: comp_req__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. tool_req:: This is a test
   :id: tool_req__test_good_1
   :status: valid
   :safety: QM



#EXPECT-NOT: pattern

.. tool_req:: This is a test
   :id: tool_req__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern
.. aou_req:: This is a test
   :id: aou_req__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. aou_req:: This is a test
   :id: aou_req__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. feat_arc_dyn:: This is a test
   :id: feat_arc_dyn__test_good_1
   :status: valid
   :safety: QM



#EXPECT-NOT: pattern

.. feat_arc_dyn:: This is a test
   :id: feat_arc_dyn__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. logic_arc_int:: This is a test
   :id: logic_arc_int__test_good_1
   :status: valid
   :safety: QM



#EXPECT-NOT: pattern

.. logic_arc_int:: This is a test
   :id: logic_arc_int__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. logic_arc_int_op:: This is a test
   :id: logic_arc_int_op__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. logic_arc_int_op:: This is a test
   :id: logic_arc_int_op__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. comp_arc_sta:: This is a test
   :id: comp_arc_sta__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. comp_arc_sta:: This is a test
   :id: comp_arc_sta__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. comp_arc_dyn:: This is a test
   :id: comp_arc_dyn__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. comp_arc_dyn:: This is a test
   :id: comp_arc_dyn__test_good_2
   :status: valid
   :safety: ASIL_B



#EXPECT-NOT: pattern

.. real_arc_int:: This is a test
   :id: real_arc_int__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. real_arc_int:: This is a test
   :id: real_arc_int__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. real_arc_int_op:: This is a test
   :id: real_arc_int_op__test_good_1
   :status: valid
   :safety: QM

#EXPECT-NOT: pattern

.. real_arc_int_op:: This is a test
   :id: real_arc_int_op__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. dd_sta:: This is a test
   :id: dd_sta__test_good_1
   :status: valid
   :safety: QM

#EXPECT-NOT: pattern

.. dd_sta:: This is a test
   :id: dd_sta__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. dd_dyn:: This is a test
   :id: dd_dyn__test_good_1
   :status: valid
   :safety: QM

#EXPECT-NOT: pattern

.. dd_dyn:: This is a test
   :id: dd_dyn__test_good_2
   :status: valid
   :safety: ASIL_B


#EXPECT-NOT: pattern

.. sw_unit:: This is a test
   :id: sw_unit__test_good_1
   :status: valid
   :safety: QM


#EXPECT-NOT: pattern

.. sw_unit:: This is a test
   :id: sw_unit__test_good_2
   :status: valid
   :safety: ASIL_B



..
   Ensuring that empty content is detected correctly
.. #EXPECT: stkh_req__test_no_content: is missing required attribute: `content`
..
.. .. stkh_req:: This is a test
..    :id: stkh_req__test_no_content
..    :status: valid
..    :safety: QM


..
   Ensuring that non empty content is detected correctly
#EXPECT-NOT: attribute: `content`

.. stkh_req:: This is a test
   :id: stkh_req__test_content
   :status: valid
   :safety: QM

   Some content, to not trigger the warning


..
   This should not trigger, as 'std_wp' is not checked for content
#EXPECT-NOT: attribute: `content`

.. std_wp:: This is a test
   :id: std_wp__test_content


#EXPECT: feat_req__random_id3.valid_from (2035-03): does not follow pattern

.. feat_req:: milestone must be a version
   :id: feat_req__random_id3
   :valid_from: 2035-03


#EXPECT: feat_req__random_id4.valid_until (2035-03): does not follow pattern

.. feat_req:: milestone must be a version
   :id: feat_req__random_id4
   :valid_until: 2035-03


.. Security Analysis: feat_sec_threat

#EXPECT: feat_sec_threat__test__bad_1: is missing required attribute: `threat_id`.

.. feat_sec_threat:: Missing threat_id
   :id: feat_sec_threat__test__bad_1
   :status: valid

   Some content.


#EXPECT: feat_sec_threat__test__bad_2.status (done): does not follow pattern `^(valid|invalid)$`.

.. feat_sec_threat:: Invalid status
   :id: feat_sec_threat__test__bad_2
   :threat_id: MT_01_03
   :status: done

   Some content.


#EXPECT-NOT: feat_sec_threat__test__ok_3

.. feat_sec_threat:: Valid threat
   :id: feat_sec_threat__test__ok_3
   :threat_id: MT_01_03
   :status: valid

   message timing is manipulated (Tampering)


.. Security Analysis: feat_sec_ana

#EXPECT: feat_sec_ana__test__bad_4: is missing required attribute: `threat_scenario_id`.

.. feat_sec_ana:: Missing threat_scenario_id
   :id: feat_sec_ana__test__bad_4
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized access to stored data.

   Argument why mitigation is insufficient.


#EXPECT: feat_sec_ana__test__bad_5.sufficient (maybe): does not follow pattern `^(yes|no)$`.

.. feat_sec_ana:: Invalid sufficient value
   :id: feat_sec_ana__test__bad_5
   :threat_scenario_id: SC_01_02
   :status: valid
   :sufficient: maybe
   :threat_effect: Unauthorized access to stored data.

   Argument why mitigation is insufficient.


#EXPECT: feat_sec_ana__test__bad_6.status (done): does not follow pattern `^(valid|invalid)$`.

.. feat_sec_ana:: Invalid status value
   :id: feat_sec_ana__test__bad_6
   :threat_scenario_id: SC_01_02
   :status: done
   :sufficient: no
   :threat_effect: Unauthorized access to stored data.

   Argument why mitigation is insufficient.


#EXPECT: feat_sec_ana__test__bad_7: is missing required attribute: `threat_effect`.

.. feat_sec_ana:: Missing threat_effect
   :id: feat_sec_ana__test__bad_7
   :threat_scenario_id: SC_01_02
   :status: invalid
   :sufficient: no

   Argument why mitigation is insufficient.


#EXPECT-NOT: feat_sec_ana__test__ok_8

.. feat_sec_ana:: Valid threat scenario
   :id: feat_sec_ana__test__ok_8
   :threat_scenario_id: SC_01_02
   :status: valid
   :sufficient: yes
   :threat_effect: Unauthorized access to stored data.

   Mitigation is sufficient because access controls are in place.


#EXPECT-NOT: feat_sec_ana__test__ok_9

.. feat_sec_ana:: Valid threat scenario with optional mitigation_issue
   :id: feat_sec_ana__test__ok_9
   :threat_scenario_id: SC_01_03
   :status: invalid
   :sufficient: no
   :threat_effect: Data integrity violation via tampering.
   :mitigation_issue: https://github.com/eclipse-score/score/issues/1

   Mitigation not yet implemented.


#EXPECT: feat_sec_ana__test__bad_10.mitigation_issue (https://github.com/eclipse-score/docs-as-code/pull/508): does not follow pattern

.. feat_sec_ana:: Invalid mitigation_issue (pull request, not issue)
   :id: feat_sec_ana__test__bad_10
   :threat_scenario_id: SC_01_04
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized data access.
   :mitigation_issue: https://github.com/eclipse-score/docs-as-code/pull/508

   Mitigation not yet implemented.


#EXPECT: feat_sec_ana__test__bad_11: is missing required attribute: `content`.

.. feat_sec_ana:: Missing argument content
   :id: feat_sec_ana__test__bad_11
   :threat_scenario_id: SC_01_04
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized data access.

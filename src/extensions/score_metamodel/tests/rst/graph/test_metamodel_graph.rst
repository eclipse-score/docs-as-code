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

#CHECK: check_metamodel_graph


.. Checks if the child requirement has the at least the same safety level as the parent requirement. It's allowed to "overfill" the safety level of the parent.
.. ASIL decomposition is not foreseen in S-CORE. Therefore it's not allowed to have a child requirement with a lower safety level than the parent requirement as
.. it is possible in an decomposition case.
.. feat_req:: Parent requirement QM
   :id: feat_req__parent__QM
   :safety: QM
   :status: valid

.. feat_req:: Parent requirement ASIL_B
   :id: feat_req__parent__ASIL_B
   :safety: ASIL_B
   :status: valid



.. Positive Test: Child requirement QM. Parent requirement has the correct related safety level. Parent requirement is `QM`.
#EXPECT-NOT: feat_req__child__1: Parent need `feat_req__parent__QM` does not fulfill condition `safety == QM`. Explanation: An ASIL requirement must link at least one parent/upstream ASIL requirement for correct decomposition. Please ensure the parent’s safety level is QM and its status is valid.

.. feat_req:: Child requirement 1
   :id: feat_req__child__1
   :safety: QM
   :satisfies: feat_req__parent__QM
   :status: valid


.. Positive Test: Child requirement ASIL B. Parent requirement has the correct related safety level. Parent requirement is `QM`.
#EXPECT-NOT: feat_req__child__2: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety == QM`. Explanation: An ASIL requirement must link at least one parent/upstream ASIL requirement for correct decomposition. Please ensure the parent’s safety level is QM and its status is valid.

.. feat_req:: Child requirement 2
   :id: feat_req__child__2
   :safety: ASIL_B
   :satisfies: feat_req__parent__ASIL_B
   :status: valid



.. Negative Test: Child requirement QM. Parent requirement is `ASIL_B`. Child cant fulfill the safety level of the parent.
#EXPECT: QM requirements cannot satisfy ASIL requirements.

.. comp_req:: Child requirement 3
   :id: feat_req__qm_child_with_asil_parent
   :safety: QM
   :satisfies: feat_req__parent__ASIL_B
   :status: valid



.. Parent requirement does not exist
#EXPECT: unknown outgoing link

.. feat_req:: Child requirement 4
   :id: feat_req__linking_to_unknown_parent
   :safety: ASIL_B
   :status: valid
   :satisfies: feat_req__parent0__abcd



.. Mitigation of Safety Analysis (FMEA and DFA) shall be checked. Mitigation shall have the same or higher safety level than the analysed item.
.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_dfa__child__5: Parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_dfa:: Child requirement 5
   :id: feat_saf_dfa__child__5
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM


.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_dfa__child__6: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_dfa:: Child requirement 6
   :id: feat_saf_dfa__child__6
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B



.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: comp_saf_dfa__child__7: Parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. comp_saf_dfa:: Child requirement 7
   :id: comp_saf_dfa__child__7
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM


.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: comp_saf_dfa__child__8: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. comp_saf_dfa:: Child requirement 8
   :id: comp_saf_dfa__child__8
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B



.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_dfa__child__9: Parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_dfa:: Child requirement 9
   :id: feat_saf_dfa__child__9
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM


.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_dfa__child__10: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_dfa:: Child requirement 10
   :id: feat_saf_dfa__child__10
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B



.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_fmea__child__11: Parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_fmea:: Child requirement 11
   :id: feat_saf_fmea__child__11
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM


.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_fmea__child__12: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_fmea:: Child requirement 12
   :id: feat_saf_fmea__child__12
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B



.. Positive Test: Linked to a mitigation that is higher to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_fmea__child__13: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. feat_saf_fmea:: Child requirement 13
   :id: feat_saf_fmea__child__13
   :safety: QM
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: comp_saf_fmea__child__14: Parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. comp_saf_fmea:: Child requirement 14
   :id: comp_saf_fmea__child__14
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM


.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: comp_saf_fmea__child__15: Parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`. Explanation: An ASIL_B safety requirement must link to a ASIL_B requirement. Please ensure that the linked requirements safety level is not QM and it's status is valid.

.. comp_saf_fmea:: Child requirement 15
   :id: comp_saf_fmea__child__15
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B

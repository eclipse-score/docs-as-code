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
#EXPECT-NOT: feat_req__child__1: parent need `feat_req__parent__QM` does not fulfill condition `safety == QM`.

.. feat_req:: Child requirement 1
   :id: feat_req__child__1
   :safety: QM
   :satisfies: feat_req__parent__QM
   :status: valid

.. Positive Test: Child requirement ASIL B. Parent requirement has the correct related safety level. Parent requirement is `QM`.
#EXPECT-NOT: feat_req__child__2: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety == QM`.

.. feat_req:: Child requirement 2
   :id: feat_req__child__2
   :safety: ASIL_B
   :satisfies: feat_req__parent__ASIL_B
   :status: valid


.. Negative Test: Child requirement QM. Parent requirement is `ASIL_B`. Child cant fulfill the safety level of the parent.
#EXPECT: feat_req__child__4: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety == QM`.

.. comp_req:: Child requirement 4
   :id: feat_req__child__4
   :safety: QM
   :satisfies: feat_req__parent__ASIL_B
   :status: valid





.. Parent requirement does not exist
#EXPECT: feat_req__child__9: Parent need `feat_req__parent0__abcd` not found in needs_dict.

.. feat_req:: Child requirement 9
   :id: feat_req__child__9
   :safety: ASIL_B
   :status: valid
   :satisfies: feat_req__parent0__abcd


.. Mitigation of Safety Analysis (FMEA and DFA) shall be checked. Mitigation shall have the same or higher safety level than the analysed item.
.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_dfa__child__10: parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`.

.. feat_saf_dfa:: Child requirement 10
   :id: feat_saf_dfa__child__10
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM

.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_dfa__child__11: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. feat_saf_dfa:: Child requirement 11
   :id: feat_saf_dfa__child__11
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: comp_saf_dfa__child__13: parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`.

.. comp_saf_dfa:: Child requirement 13
   :id: comp_saf_dfa__child__13
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM

.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: comp_saf_dfa__child__14: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. comp_saf_dfa:: Child requirement 14
   :id: comp_saf_dfa__child__14
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_dfa__child__16: parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`.

.. feat_saf_dfa:: Child requirement 16
   :id: feat_saf_dfa__child__16
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM

.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_dfa__child__17: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. feat_saf_dfa:: Child requirement 17
   :id: feat_saf_dfa__child__17
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: feat_saf_fmea__child__19: parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`.

.. feat_saf_fmea:: Child requirement 19
   :id: feat_saf_fmea__child__19
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM

.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_fmea__child__20: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. feat_saf_fmea:: Child requirement 20
   :id: feat_saf_fmea__child__20
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


.. Positive Test: Linked to a mitigation that is higher to the safety level of the analysed item.
#EXPECT-NOT: feat_saf_fmea__child__21: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. feat_saf_fmea:: Child requirement 21
   :id: feat_saf_fmea__child__21
   :safety: QM
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B

.. Negative Test: Linked to a mitigation that is lower than the safety level of the analysed item.
#EXPECT: comp_saf_fmea__child__22: parent need `feat_req__parent__QM` does not fulfill condition `safety != QM`.

.. comp_saf_fmea:: Child requirement 22
   :id: comp_saf_fmea__child__22
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__QM

.. Positive Test: Linked to a mitigation that is equal to the safety level of the analysed item.
#EXPECT-NOT: comp_saf_fmea__child__23: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != QM`.

.. comp_saf_fmea:: Child requirement 23
   :id: comp_saf_fmea__child__23
   :safety: ASIL_B
   :status: valid
   :mitigated_by: feat_req__parent__ASIL_B


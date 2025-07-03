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

.. feat_req:: Parent requirement ASIL_D
   :id: feat_req__parent__ASIL_D
   :safety: ASIL_D
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

.. Positive Test: Child requirement ASIL D. Parent requirement has the correct related safety level. Parent requirement is `QM`.
#EXPECT-NOT: feat_req__child__3: parent need `feat_req__parent__ASIL_D` does not fulfill condition `safety == QM`.

.. feat_req:: Child requirement 3
   :id: feat_req__child__3
   :safety: ASIL_D
   :satisfies: feat_req__parent__ASIL_D
   :status: valid

.. Negative Test: Child requirement QM. Parent requirement is `ASIL_B`. Child cant fulfill the safety level of the parent.
#EXPECT: feat_req__child__4: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety == QM`.

.. comp_req:: Child requirement 4
   :id: feat_req__child__4
   :safety: QM
   :satisfies: feat_req__parent__ASIL_B
   :status: valid

.. Negative Test: Child requirement QM. Parent requirement is `ASIL_D`. Child cant fulfill the safety level of the parent.
#EXPECT: feat_req__child__5: parent need `feat_req__parent__ASIL_D` does not fulfill condition `safety == QM`.

.. comp_req:: Child requirement 5
   :id: feat_req__child__5
   :safety: QM
   :satisfies: feat_req__parent__ASIL_D
   :status: valid

.. Positive Test: Child requirement ASIL_B. Parent requirement has the correct related safety level. Parent requirement is `QM`.
#EXPECT-NOT: feat_req__child__6: parent need `feat_req__parent__QM` does not fulfill condition `safety != ASIL_D`.

.. feat_req:: Child requirement 6
   :id: feat_req__child__6
   :safety: ASIL_B
   :satisfies: feat_req__parent__QM
   :status: valid

.. Positive Test: Child requirement ASIL_B. Parent requirement has the correct related safety level. Parent requirement is `ASIL_B`.
#EXPECT-NOT: feat_req__child__7: parent need `feat_req__parent__ASIL_B` does not fulfill condition `safety != ASIL_D`.

.. feat_req:: Child requirement 7
   :id: feat_req__child__7
   :safety: ASIL_B
   :satisfies: feat_req__parent__ASIL_B
   :status: valid

.. Negative Test: Child requirement ASIL_B. Parent requirement is `ASIL_D`. Child cant fulfill the safety level of the parent.
#EXPECT: feat_req__child__8: parent need `feat_req__parent__ASIL_D` does not fulfill condition `safety != ASIL_D`.

.. comp_req:: Child requirement 8
   :id: feat_req__child__8
   :safety: ASIL_B
   :satisfies: feat_req__parent__ASIL_D
   :status: valid



.. Parent requirement does not exist
#EXPECT: feat_req__child__9: Parent need `feat_req__parent0__abcd` not found in needs_dict.

.. feat_req:: Child requirement 9
   :id: feat_req__child__9
   :safety: ASIL_B
   :status: valid
   :satisfies: feat_req__parent0__abcd




.. Parent requirement does not exist
#EXPECT: feat_saf_dfa__child__10: Parent need `feat_req__parent__QM` does not fulfill the condition `safety != QM`.

.. feat_req:: Child requirement 10
   :id: feat_saf_dfa__child__10
   :safety: ASIL_B
   :mitigates: feat_req__parent__QM

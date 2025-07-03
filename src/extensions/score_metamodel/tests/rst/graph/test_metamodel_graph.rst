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

.. feat_req:: Parent requirement
   :id: feat_req__parent__abcd
   :safety: QM
   :status: valid

.. Parent requirement has the correct safety level
#EXPECT-NOT: feat_req__child__abce: parent need `feat_req__parent__abcd` does not fulfill condition `{'and': ['safety == QM']}`.

.. feat_req:: Child requirement
   :id: feat_req__child__abce
   :safety: QM
   :satisfies: feat_req__parent__abcd
   :status: valid

.. feat_req:: Parent requirement2
   :id: feat_req__parent__abcd2
   :safety: QM
   :status: valid

.. Parent requirement has the correct safety level
#EXPECT-NOT: feat_req__child__abce2: parent need `feat_req__parent__abcd2` does not fulfill condition `{'and': ['safety == QM']}`.

.. feat_req:: Child requirement2
   :id: feat_req__child__abce2
   :safety: ASIL_B
   :satisfies: feat_req__parent__abcd2
   :status: valid

.. feat_req:: Parent requirement3
   :id: feat_req__parent3__abcd
   :safety: ASIL_B
   :status: valid

.. Graph check without combined condition (no and or or)
#EXPECT: feat_req__child__abce3: parent need `feat_req__parent3__abcd` does not fulfill condition `safety == QM`.

.. comp_req:: Child requirement3
   :id: feat_req__child__abce3
   :safety: QM
   :satisfies: feat_req__parent3__abcd
   :status: valid
















.. .. feat_req:: Parent requirement 2
..    :id: feat_req__parent2__abcd
..    :safety: QM

.. .. Parent requirement has the correct safety level
.. #EXPECT-NOT: feat_req__child2__abce: parent need `feat_req__parent2__abcd` does not fulfill condition

.. .. feat_req:: Child requirement 2
..    :id: feat_req__child2__abce
..    :safety: QM
..    :satisfies: feat_req__parent2__abcd

.. .. Parent requirement does not exist
.. #EXPECT: feat_req__child3__abce: Parent need `feat_req__parent0__abcd` not found in needs_dict.

.. .. feat_req:: Child requirement 3
..    :id: feat_req__child3__abce
..    :safety: ASIL_B
..    :status: valid
..    :satisfies: feat_req__parent0__abcd

.. .. feat_req:: Parent requirement 3
..    :id: feat_req__parent3__abcd
..    :status: invalid

.. .. Graph check without combined condition (no and or or)
.. #EXPECT: comp_req__parent4__abcd: parent need `feat_req__parent3__abcd` does not fulfill condition `status == valid`.

.. .. comp_req:: Child requirement 4
..    :id: comp_req__parent4__abcd
..    :status: valid
..    :satisfies: feat_req__parent3__abcd

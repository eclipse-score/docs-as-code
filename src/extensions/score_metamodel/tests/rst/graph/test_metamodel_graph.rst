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

.. test_metadata::
   :id: test_metadata__metamodel_graph_checks
   :partially_verifies_list: LACKS TOOL REQ
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests if metamodel graph checks work as defined / intended


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

.. feat_req:: Child requirement 1
   :id: feat_req__child__1
   :safety: QM
   :derived_from: feat_req__parent__QM
   :status: valid
   :expect_not: safety requirement


.. Positive Test: Child requirement ASIL B. Parent requirement has the correct related safety level. Parent requirement is `QM`.

.. feat_req:: Child requirement 2
   :id: feat_req__child__2
   :safety: ASIL_B
   :derived_from: feat_req__parent__ASIL_B
   :status: valid
   :expect_not: safety



.. Negative Test: Child requirement QM. Parent requirement is `ASIL_B`. Child cant fulfill the safety level of the parent.

.. comp_req:: Child requirement 3
   :id: feat_req__qm_child_with_asil_parent
   :safety: QM
   :derived_from: feat_req__parent__ASIL_B
   :status: valid
   :expect: QM requirements cannot be derived from ASIL requirements.



.. Parent requirement does not exist

.. feat_req:: Child requirement 4
   :id: feat_req__linking_to_unknown_parent
   :safety: ASIL_B
   :status: valid
   :derived_from: feat_req__parent0__abcd
   :expect: unknown outgoing link

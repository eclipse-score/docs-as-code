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

#CHECK: check_metamodel_graph

.. feat_req:: QM Feature Requirement Parent
   :id: feat_req__test__qm_parent
   :safety: QM
   :status: valid

.. feat_req:: Safety Feature Requirement Parent
   :id: feat_req__test__asil_parent
   :safety: ASIL_B
   :status: valid

.. comp_req:: QM Component Requirement Parent
   :id: comp_req__test__qm_parent
   :safety: QM
   :status: valid

.. comp_req:: Safety Component Requirement Parent
   :id: comp_req__test__asil_parent
   :safety: ASIL_B
   :status: valid


.. Negative Test: Safety feat_arc_sta fulfils a QM feat_req — should warn.
#EXPECT: feat_arc_sta__test__safety_to_qm: Parent need `feat_req__test__qm_parent` does not fulfill condition `safety != QM`.

.. feat_arc_sta:: Safety view with QM parent
   :id: feat_arc_sta__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__test__qm_parent


.. Positive Test: Safety feat_arc_sta fulfils a safety feat_req — should not warn.
#EXPECT-NOT: fulfil

.. feat_arc_sta:: Safety view with safety parent
   :id: feat_arc_sta__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__test__asil_parent


.. Positive Test: QM feat_arc_sta — check does not apply to QM elements.
#EXPECT-NOT: fulfil

.. feat_arc_sta:: QM view with QM parent
   :id: feat_arc_sta__test__qm_to_qm
   :safety: QM
   :security: NO
   :status: valid
   :fulfils: feat_req__test__qm_parent


.. Negative Test: Safety feat_arc_dyn fulfils a QM feat_req — should warn.
#EXPECT: feat_arc_dyn__test__safety_to_qm: Parent need `feat_req__test__qm_parent` does not fulfill condition `safety != QM`.

.. feat_arc_dyn:: Safety dynamic view with QM parent
   :id: feat_arc_dyn__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__test__qm_parent


.. Positive Test: Safety feat_arc_dyn fulfils a safety feat_req — should not warn.
#EXPECT-NOT: fulfil

.. feat_arc_dyn:: Safety dynamic view with safety parent
   :id: feat_arc_dyn__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: feat_req__test__asil_parent


.. Positive Test: QM feat_arc_dyn — check does not apply to QM elements.
#EXPECT-NOT: fulfil

.. feat_arc_dyn:: QM dynamic view with QM parent
   :id: feat_arc_dyn__test__qm_to_qm
   :safety: QM
   :security: NO
   :status: valid
   :fulfils: feat_req__test__qm_parent


.. Negative Test: Safety comp_arc_sta fulfils a QM comp_req — should warn.
#EXPECT: comp_arc_sta__test__safety_to_qm: Parent need `comp_req__test__qm_parent` does not fulfill condition `safety != QM`.

.. comp_arc_sta:: Safety component view with QM parent
   :id: comp_arc_sta__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: comp_req__test__qm_parent


.. Positive Test: Safety comp_arc_sta fulfils a safety comp_req — should not warn.
#EXPECT-NOT: fulfil

.. comp_arc_sta:: Safety component view with safety parent
   :id: comp_arc_sta__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: comp_req__test__asil_parent


.. Negative Test: Safety comp_arc_dyn fulfils a QM comp_req — should warn.
#EXPECT: comp_arc_dyn__test__safety_to_qm: Parent need `comp_req__test__qm_parent` does not fulfill condition `safety != QM`.

.. comp_arc_dyn:: Safety dynamic component view with QM parent
   :id: comp_arc_dyn__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: comp_req__test__qm_parent


.. Positive Test: Safety comp_arc_dyn fulfils a safety comp_req — should not warn.
#EXPECT-NOT: fulfil

.. comp_arc_dyn:: Safety dynamic component view with safety parent
   :id: comp_arc_dyn__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :fulfils: comp_req__test__asil_parent

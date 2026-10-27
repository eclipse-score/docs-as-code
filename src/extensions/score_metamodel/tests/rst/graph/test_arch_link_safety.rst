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
   :id: test_metadata__arch_link_safety
   :fully_verifies_list: tool_req__docs_req_arch_link_safety_to_arch[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks that valid safety architecture elements implement only valid safety
   architecture elements.
   A valid safety link is accepted, while links to a QM or invalid target are
   rejected.


.. logic_arc_int:: Safety logical interface
   :id: logic_arc_int__arch_sec__safety_interface
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1


.. logic_arc_int_op:: Valid safety logical operation
   :id: logic_arc_int_op__arch_sec__safety_valid
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :included_by: logic_arc_int__arch_sec__safety_interface


.. logic_arc_int_op:: QM logical operation
   :id: logic_arc_int_op__arch_sec__safety_qm
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :included_by: logic_arc_int__arch_sec__safety_interface


.. logic_arc_int_op:: Invalid safety logical operation
   :id: logic_arc_int_op__arch_sec__safety_invalid
   :security: NO
   :safety: ASIL_B
   :status: invalid
   :version: 1
   :included_by: logic_arc_int__arch_sec__safety_interface


.. real_arc_int:: Safety real interface
   :id: real_arc_int__arch_sec__safety_real_interface
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :language: cpp


.. real_arc_int_op:: Safety operation implements valid safety operation
   :id: real_arc_int_op__arch_sec__safety_src_valid
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :included_by: real_arc_int__arch_sec__safety_real_interface
   :implements: logic_arc_int_op__arch_sec__safety_valid
   :expect_not: does not fulfill condition


.. real_arc_int_op:: Safety operation implements QM operation
   :id: real_arc_int_op__arch_sec__safety_src_qm
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :included_by: real_arc_int__arch_sec__safety_real_interface
   :implements: logic_arc_int_op__arch_sec__safety_qm
   :expect: does not fulfill condition


.. real_arc_int_op:: Safety operation implements invalid safety operation
   :id: real_arc_int_op__arch_sec__safety_src_invalid
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :included_by: real_arc_int__arch_sec__safety_real_interface
   :implements: logic_arc_int_op__arch_sec__safety_invalid
   :expect: does not fulfill condition


.. feat:: Safety feature
   :id: feat__arch_sec__safety_feature
   :security: NO
   :safety: QM
   :status: valid
   :version: 1


.. logic_arc_int:: QM logical interface
   :id: logic_arc_int__arch_sec__safety_qm_interface
   :security: NO
   :safety: QM
   :status: valid
   :version: 1


.. logic_arc_int:: Invalid safety logical interface
   :id: logic_arc_int__arch_sec__safety_invalid_interface
   :security: NO
   :safety: ASIL_B
   :status: invalid
   :version: 1


.. comp:: Safety component implements valid safety logical interface
   :id: comp__arch_sec__safety_comp_valid
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :belongs_to: feat__arch_sec__safety_feature
   :implements: logic_arc_int__arch_sec__safety_interface
   :expect_not: does not fulfill condition


.. comp:: Safety component implements QM logical interface
   :id: comp__arch_sec__safety_comp_qm
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :belongs_to: feat__arch_sec__safety_feature
   :implements: logic_arc_int__arch_sec__safety_qm_interface
   :expect: does not fulfill condition


.. comp:: Safety component implements invalid safety logical interface
   :id: comp__arch_sec__safety_comp_invalid
   :security: NO
   :safety: ASIL_B
   :status: valid
   :version: 1
   :belongs_to: feat__arch_sec__safety_feature
   :implements: logic_arc_int__arch_sec__safety_invalid_interface
   :expect: does not fulfill condition

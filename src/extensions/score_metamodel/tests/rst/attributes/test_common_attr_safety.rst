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


.. test_metadata:: Test Common Attribute Safety
   :id: test_metadata__common_attr_safety
   :fully_verifies_list: tool_req__docs_common_attr_safety
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the safety attribute only accepts the values QM and ASIL_B.
   The rule applies to all requirement types except process and tool
   requirements, and to all architecture element types.



.. stkh_req:: Safety QM
   :id: stkh_req__common_attr_safety__qm
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: valid safety value
   :valid_from: v1.0
   :expect_not: does not follow pattern

.. stkh_req:: Safety ASIL_B
   :id: stkh_req__common_attr_safety__asil_b
   :version: 1
   :reqtype: Functional
   :safety: ASIL_B
   :security: NO
   :status: valid
   :rationale: valid safety value
   :valid_from: v1.0
   :expect_not: does not follow pattern

.. stkh_req:: Safety YES
   :id: stkh_req__common_attr_safety__bad
   :version: 1
   :reqtype: Functional
   :safety: YES
   :security: NO
   :status: valid
   :rationale: invalid safety value
   :valid_from: v1.0
   :expect: does not follow pattern


.. feat_req:: Safety YES
   :id: feat_req__common_attr_safety__bad
   :version: 1
   :reqtype: Functional
   :safety: True
   :security: NO
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__brake
   :expect: does not follow pattern

   Invalid safety value YES.


.. comp_req:: Safety YES
   :id: comp_req__common_attr_safety__bad
   :version: 1
   :reqtype: Functional
   :safety: safe
   :security: NO
   :status: valid
   :satisfied_by: comp__smoke
   :expect: does not follow pattern

   Invalid safety value YES.


.. aou_req:: Safety YES
   :id: aou_req__common_attr_safety__bad
   :version: 1
   :reqtype: Functional
   :safety: ASIL
   :security: NO
   :status: valid
   :expect: does not follow pattern

   Invalid safety value YES.


.. feat:: Safety YES
   :id: feat__brake
   :version: 1
   :safety: unsafe
   :security: NO
   :status: valid
   :expect: does not follow pattern


.. feat_arc_sta:: Safety YES
   :id: feat_arc_sta__common_attr_safety__bad
   :version: 1
   :safety: NO
   :security: NO
   :status: valid
   :includes: logic_arc_int__raw, logic_arc_int_op__flip
   :belongs_to: feat__brake
   :expect: does not follow pattern


.. logic_arc_int:: Safety YES
   :id: logic_arc_int__raw
   :version: 1
   :safety: ISO26262
   :security: NO
   :status: valid
   :expect: does not follow pattern


.. logic_arc_int_op:: Safety YES
   :id: logic_arc_int_op__flip
   :version: 1
   :safety: invalid
   :security: NO
   :status: valid
   :included_by: logic_arc_int__raw
   :expect: does not follow pattern


.. comp_arc_sta:: Safety YES
   :id: comp_arc_sta__common_attr_safety__bad
   :version: 1
   :safety: draft
   :security: NO
   :status: valid
   :belongs_to: comp__smoke
   :expect: does not follow pattern


.. comp:: Safety YES
   :id: comp__smoke
   :version: 1
   :safety: tbd
   :security: NO
   :status: valid
   :belongs_to: feat__brake
   :expect: does not follow pattern


.. real_arc_int:: Safety YES
   :id: real_arc_int__eth
   :version: 1
   :safety: bla
   :security: NO
   :status: valid
   :language: cpp
   :expect: does not follow pattern


.. real_arc_int_op:: Safety YES
   :id: real_arc_int_op__erase
   :version: 1
   :safety: unclear
   :security: NO
   :status: valid
   :included_by: real_arc_int__eth
   :expect: does not follow pattern

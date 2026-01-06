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

.. stkh_req:: Test Stakeholder Requirement 1
   :id: stkh_req__test_stakeholder_requirement_1__basic_stkh_req
   :reqtype: Non-Functional
   :safety: ASIL_B
   :security: YES
   :rationale: Exists just for the test the component / feature drawings
   :status: invalid

.. feat_req:: Test Feature Requirement 1
   :id: feat_req__test_feature_1__test_req_1
   :reqtype: Process
   :security: YES
   :safety: ASIL_B
   :satisfies: stkh_req__test_stakeholder_requirement_1__basic_stkh_req
   :status: invalid

   Test Feature Requirement 1

.. feat:: Test Feature 1
   :id: feat__test_feature_1
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :includes: logic_arc_int__test_feature_1__test_interface_1, logic_arc_int_op__test_feature_1__test_operation_1
   :consists_of: comp__test_component_1, comp__test_component_2

.. feat_arc_sta:: Test Feature Static View Feature 1
   :id: feat_arc_sta__test_feature_1__static_view
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :fulfils: feat_req__test_feature_1__test_req_1
   :includes: logic_arc_int__test_feature_1__test_interface_1

   .. needarch
      :scale: 50
      :align: center

      {{ draw_feature(need(), needs) }}

.. feat_arc_dyn:: Test Feature Static Dynamic Feature 1
   :id: feat_arc_dyn__test_feature_1__dynamic_view
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :fulfils: feat_req__test_feature_1__test_req_1

   Put here a sequence diagram

.. logic_arc_int:: Logic Interface Test 1
   :id: logic_arc_int__test_feature_1__test_interface_1
   :security: YES
   :safety: ASIL_B
   :status: invalid

.. logic_arc_int_op:: Logic Operation Test 1
   :id: logic_arc_int_op__test_feature_1__test_operation_1
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :included_by: logic_arc_int__test_feature_1__test_interface_1

.. logic_arc_int:: Logic Interface Test 2
   :id: logic_arc_int__test_feature_1__test_interface_2
   :security: YES
   :safety: ASIL_B
   :status: invalid

Component 1
~~~~~~~~~~~

.. comp:: Test Component 1
   :id: comp__test_component_1
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :implements: logic_arc_int__test_feature_1__test_interface_1
   :uses: logic_arc_int__test_feature_1__test_interface_2
   :consists_of: sw_unit__component_1__test_unit_1, comp__test_sub_component_1

.. comp_req:: Test Component 1 Requirement 1
   :id: comp_req__test_component_1__requirement_1
   :reqtype: Process
   :security: YES
   :safety: ASIL_B
   :satisfies: feat_req__test_feature_1__test_req_1
   :status: invalid

   Test Component 1 Requirement

.. sw_unit:: SW Test Unit 1
   :id: sw_unit__component_1__test_unit_1
   :security: YES
   :safety: ASIL_B
   :status: invalid

.. comp:: Test Sub Component 1
   :id: comp__test_sub_component_1
   :security: YES
   :safety: ASIL_B
   :status: invalid
   :implements: logic_arc_int__test_feature_1__test_interface_1
   :consists_of: sw_unit__sub_component_1__test_unit_2

.. comp_arc_sta:: Test Component Architecture Component 1
   :id: comp_arc_sta__feature_name__component_name
   :safety: ASIL_B
   :security: YES
   :status: invalid
   :fulfils: comp_req__test_component_1__requirement_1
   :implements: logic_arc_int__test_feature_1__test_interface_1
   :belongs_to: comp__test_sub_component_1

.. sw_unit:: SW Test Unit 2
   :id: sw_unit__sub_component_1__test_unit_2
   :security: YES
   :safety: ASIL_B
   :status: invalid

Component 1
~~~~~~~~~~~

.. comp:: Test Component 2
   :id: comp__test_component_2
   :security: YES
   :safety: QM
   :status: invalid
   :implements: logic_arc_int__test_feature_1__test_interface_2

.. mod:: Feature Test Module 1
   :id: mod__test_feature_1_module_1
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: comp__test_component_1, comp__test_component_2

.. mod_view_sta:: Feature Test Module 1 Static View
   :id: mod_view_sta__test_feature_1_module_1__test_static_view_1
   :belongs_to: mod__test_feature_1_module_1
   :includes: comp_arc_sta__feature_name__component_name

   .. needarch
      :scale: 50
      :align: center

      {{ draw_module(need(), needs) }}

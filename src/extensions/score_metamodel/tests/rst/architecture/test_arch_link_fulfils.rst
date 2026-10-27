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
   :id: test_metadata__arch_link_fulfils
   :fully_verifies_list: tool_req__docs_arch_link_fulfils[version==3]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks the allowed ``fulfils`` target type for each architecture source type.
   Each permitted source-target combination is accepted, and mismatched feature
   and component requirement targets are rejected.


.. feat:: Feature
   :id: feat__arch_fulfils__feature
   :security: NO
   :safety: QM
   :status: valid


.. comp:: Component
   :id: comp__arch_fulfils__component
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__arch_fulfils__feature


.. logic_arc_int:: Logical interface
   :id: logic_arc_int__arch_fulfils__interface
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__arch_fulfils__feature


.. feat_req:: Feature requirement
   :id: feat_req__arch_fulfils__feature__good
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__arch_fulfils__feature

   A feature requirement target.


.. comp_req:: Component requirement
   :id: comp_req__arch_fulfils__component__good
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: comp__arch_fulfils__component

   A component requirement target.


.. feat_arc_sta:: Feature static view fulfils feature requirement
   :id: feat_arc_sta__arch_fulfils__good
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__arch_fulfils__feature
   :includes: logic_arc_int__arch_fulfils__interface
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect_not: but it must reference


.. feat_arc_dyn:: Feature dynamic view fulfils feature requirement
   :id: feat_arc_dyn__arch_fulfils__good
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__arch_fulfils__feature
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect_not: but it must reference


.. logic_arc_int:: Logical interface fulfils feature requirement
   :id: logic_arc_int__arch_fulfils__fulfils_good
   :security: NO
   :safety: QM
   :status: valid
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect_not: but it must reference


.. comp_arc_sta:: Component static view fulfils component requirement
   :id: comp_arc_sta__arch_fulfils__good
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__arch_fulfils__component
   :fulfils: comp_req__arch_fulfils__component__good
   :expect_not: but it must reference


.. comp_arc_dyn:: Component dynamic view fulfils component requirement
   :id: comp_arc_dyn__arch_fulfils__good
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__arch_fulfils__component
   :fulfils: comp_req__arch_fulfils__component__good
   :expect_not: but it must reference


.. real_arc_int:: Real interface fulfils component requirement
   :id: real_arc_int__arch_fulfils__good
   :security: NO
   :safety: QM
   :status: valid
   :language: cpp
   :fulfils: comp_req__arch_fulfils__component__good
   :expect_not: but it must reference


.. feat_arc_sta:: Feature static view rejects component requirement
   :id: feat_arc_sta__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__arch_fulfils__feature
   :includes: logic_arc_int__arch_fulfils__interface
   :fulfils: comp_req__arch_fulfils__component__good
   :expect: but it must reference Feature Requirement (feat_req)


.. comp_arc_sta:: Component static view rejects feature requirement
   :id: comp_arc_sta__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__arch_fulfils__component
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect: but it must reference Component Requirement (comp_req)


.. feat_arc_dyn:: Feature dynamic view rejects component requirement
   :id: feat_arc_dyn__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__arch_fulfils__feature
   :fulfils: comp_req__arch_fulfils__component__good
   :expect: but it must reference Feature Requirement (feat_req)


.. logic_arc_int:: Logical interface rejects component requirement
   :id: logic_arc_int__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :fulfils: comp_req__arch_fulfils__component__good
   :expect: but it must reference Feature Requirement (feat_req)


.. comp_arc_dyn:: Component dynamic view rejects feature requirement
   :id: comp_arc_dyn__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: comp__arch_fulfils__component
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect: but it must reference Component Requirement (comp_req)


.. real_arc_int:: Real interface rejects feature requirement
   :id: real_arc_int__arch_fulfils__bad
   :security: NO
   :safety: QM
   :status: valid
   :language: cpp
   :fulfils: feat_req__arch_fulfils__feature__good
   :expect: but it must reference Component Requirement (comp_req)

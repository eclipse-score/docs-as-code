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

.. test_metadata:: Logical interface implementation consistency
   :id: test_metadata__arch_consistency_interf
   :partially_verifies_list: tool_req__arch_consistency_interf[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   A logical interface included by a feature must have an incoming implements
   link from a component. Missing implementations produce information only.
   Interfaces without feature assignment are outside this check's scope.

.. feat:: Feature owning the logical interfaces
   :id: feat__interf_consistency
   :security: NO
   :safety: QM
   :status: valid

.. logic_arc_int:: Feature interface without an implementation
   :id: logic_arc_int__interf_consistency__missing
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__interf_consistency
   :expect_info: No linked need in `implements_back`. Explanation: A logical interface included by a feature must be implemented by at least one component.
   :expect_not: No linked need in `implements_back`

   No component implements this interface. The empty backlink list must produce
   an informational diagnostic without turning it into a build warning.

.. logic_arc_int:: Feature interface implemented by a component
   :id: logic_arc_int__interf_consistency__implemented
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__interf_consistency
   :expect_info_not: A logical interface included by a feature must be implemented by at least one component.
   :expect_not: A logical interface included by a feature must be implemented by at least one component.

.. comp:: Component implementing the feature interface
   :id: comp__interf_consistency
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__interf_consistency
   :implements: logic_arc_int__interf_consistency__implemented

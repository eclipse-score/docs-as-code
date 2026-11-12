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
   :fully_verifies_list: tool_req__arch_consistency_interf[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   A logical interface included by a feature must have an incoming implements
   link from a component. Missing implementations produce a warning.
   Each feature must be linked to at least one logical architectural interface.
   Interfaces without feature assignment are outside this check's scope.

.. feat:: Feature owning the logical interfaces
   :id: feat__interf_consistency
   :security: NO
   :safety: QM
   :status: valid
   :expect_not: A feature must have at least one logical architectural interface.

.. feat:: Feature without any logical interface
   :id: feat__arch_one
   :security: NO
   :safety: QM
   :status: valid
   :expect: No linked need in `included_by_back`. Explanation: A feature must have at least one logical architectural interface.

.. logic_arc_int:: Feature interface without an implementation
   :id: logic_arc_int__interf_consistency__missing
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__interf_consistency
   :expect: No linked need in `implements_back`. Explanation: A logical interface included by a feature must be implemented by at least one component.

   No component implements this interface. The empty backlink list must produce
   a diagnostic without turning it into a build error.

.. logic_arc_int:: Feature interface implemented by a component
   :id: logic_arc_int__interf_consistency__implemented
   :security: NO
   :safety: QM
   :status: valid
   :included_by: feat__interf_consistency
   :expect_not: A logical interface included by a feature must be implemented by at least one component.

.. comp:: Component implementing the feature interface
   :id: comp__interf_consistency
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__interf_consistency
   :implements: logic_arc_int__interf_consistency__implemented

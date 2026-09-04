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

S-CORE Modern Component
=======================

This component is mounted by the modern module and derives one of its
component requirements from the platform feature requirement. The platform
requirement is imported by the module, not by this standalone component.

.. feat:: Modern component feature
   :id: feat__modern_component
   :security: NO
   :safety: QM
   :status: valid
   :version: 1

.. comp:: Modern linked component
   :id: comp__modern_component
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :belongs_to: feat__modern_component

.. comp_req:: Modern component platform requirement
   :id: comp_req__modern_component__platform_feature
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :version: 1
   :derived_from: feat_req__platform__feature
   :satisfied_by: comp__modern_component

   The modern component requires the platform feature made available by its
   parent module.

.. tool_req:: Modern component implementation is traceable
   :id: tool_req__modern_component
   :version: 1

   The modern component implementation is covered by the component source
   code-link scan. The linked component requirement above depends on the
   platform feature requirement. The integration test checks that the
   component can be built through its module, where that requirement is
   available, but not as a standalone bundle.

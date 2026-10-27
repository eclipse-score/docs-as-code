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

S-CORE Legacy Component
=======================

This component is mounted by the legacy module, which consumes the platform
feature requirements through the legacy ``data`` API.

.. tool_req:: Legacy component implementation is traceable
   :id: tool_req__legacy_component
   :version: 1
   :satisfies: gd_req__legacy_component_traceability

   The legacy component implementation is covered by the component source
   code-link scan. The integration test checks that this link is preserved
   when the component is built through its module and by the full site.

.. gd_req:: Mounted components preserve source-code traceability
   :id: gd_req__legacy_component_traceability
   :version: 1

   Source-code traceability links of a component must survive mounting into
   its parent module and the full site.

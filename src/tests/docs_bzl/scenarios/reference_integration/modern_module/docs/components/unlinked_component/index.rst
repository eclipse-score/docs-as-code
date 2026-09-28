..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

S-CORE Modern Unlinked Component
================================

This component has no dependency on a requirement owned by another bundle.
It should therefore be buildable both independently and through the modern
module.

.. tool_req:: Modern unlinked component is self-contained
   :id: tool_req__modern_unlinked_component
   :version: 1
   :satisfies: gd_req__modern_unlinked_self_contained

   This requirement is intentionally not linked to the platform feature
   requirement. It verifies the independent-component control case.

.. gd_req:: Self-contained components build without external needs
   :id: gd_req__modern_unlinked_self_contained
   :version: 1

   A component that has no dependency on a requirement owned by another
   bundle must build both independently and through its parent module.

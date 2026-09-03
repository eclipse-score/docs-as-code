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

This component consumes platform feature requirements through the current
``external_needs`` API and is mounted by the modern module.

.. tool_req:: Modern component implementation is traceable
   :id: tool_req__modern_component
   :version: 1

   The modern component implementation is covered by the component source
   code-link scan. The integration test checks that this link is preserved
   when the component is built alone, by its module, and by the full site.

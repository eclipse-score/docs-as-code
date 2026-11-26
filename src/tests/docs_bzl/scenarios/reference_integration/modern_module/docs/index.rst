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

S-CORE Modern Module
====================

This module consumes platform feature requirements through the current
``external_needs`` API and contributes its documentation to the reference
integration.

.. toctree::
   :hidden:

   components

.. mod:: Modern module
   :id: mod__modern_module
   :version: 1
   :includes: comp__modern_component

.. mod_ver_report:: Modern module verification report
   :id: mod_vrep__docs_as_code__modern_module
   :version: 1
   :safety: QM
   :security: NO
   :status: valid
   :verification_method: Automated tests
   :belongs_to: mod__modern_module
   :post_template: module_verification_report

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


.. test_metadata:: Document Types Are Supported
   :id: test_metadata__doc_types
   :fully_verifies_list: tool_req__docs_doc_types
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that the document and doc_tool need types are available.


.. workproduct:: Generic Workproduct
   :id: wp__doc_types
   :version: 1
   :status: valid

.. document:: Generic Document Is Supported
   :id: doc__doc_type
   :version: 1
   :status: valid
   :safety: QM
   :security: NO
   :realizes: wp__doc_types
   :expect_not: is missing required attribute, is missing required link, does not follow pattern

.. doc_tool:: Tool Verification Report Is Supported
   :id: doc_tool__doc_type
   :version: 1
   :status: evaluated
   :safety_affected: NO
   :security_affected: NO
   :tcl: LOW
   :realizes: wp__doc_types
   :expect_not: is missing required attribute, is missing required link, does not follow pattern

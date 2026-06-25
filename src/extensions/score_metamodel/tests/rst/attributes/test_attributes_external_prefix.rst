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


.. test_metadata:: Test metamodel options
   :id: test_metadata__check_options
   :partially_verifies_list: tool_req__docs_common_attr_id_scheme
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests if metamodel defined 'options' regex are followed and adhered to and checked correctly

.. Test: No external prefixes (single documentation mega-build)
.. Verifies links work when all needs are loaded in one Sphinx instance, without prefix logic.

.. tool_req:: This is a test
   :id: tool_req__test_abcd
   :satisfies: doc_getstrt__req__process
   :expect_not: does not follow pattern `^doc_.+$`.

   This should not give a warning


.. Also make sure it works with lists of links

.. tool_req:: This is a test
   :id: tool_req__test_aaaa
   :satisfies: doc_getstrt__req__process;gd_guidl__req__engineering
   :expect_not: does not follow pattern `^doc_.+$`., does not follow pattern `^gd_.+$`.

   This should give a warning

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


.. test_metadata::
   :id: test_metadata__extra_options
   :partially_verifies_list: tool_req__docs_req_types, tool_req__docs_common_attr_status
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests if we probhibit / allow extra options correctly for needs


.. Invalid option: `safety` is not allowed

.. std_wp:: This is a test
   :id: std_wp__test__abcd
   :safety: QM
   :expect: std_wp__test__abcd: has these extra options: `safety`.



.. No invalid extra options are present

.. std_wp:: This is a test
   :id: std_wp__test__abce
   :expect_not: has these extra options

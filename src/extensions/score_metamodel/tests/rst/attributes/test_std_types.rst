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


.. test_metadata::
   :id: test_metadata__std_types
   :fully_verifies_list: tool_req__docs_stdreq_types[version==1], tool_req__docs_stdwp_types[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that std_req and std_wp directives are supported by the metamodel.


.. std_req:: Standard requirement
   :id: std_req__iso26262__test__001
   :status: valid
   :expect_not: unknown directive


.. std_wp:: Standard workproduct
   :id: std_wp__iso26262__test__001
   :status: valid
   :expect_not: unknown directive

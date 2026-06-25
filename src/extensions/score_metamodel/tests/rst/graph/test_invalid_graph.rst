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
   :id: test_metadata__valid_links_to_valid
   :partially_verifies_list: tool_req__docs_req_arch_link_safety_to_arch
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Checks if valid reqs only link to valid reqs
   Note: DISABLED ATM, due to check not being a 'full' warning yet



.. feat_req:: Parent requirement INVALID QM
   :id: feat_req__parent__QM_invalid
   :safety: QM
   :status: invalid



.. We can not yet enable this test. As the check is only an 'info' and not yet a true warning
.. Therefore the test is the inverse of what we will test once it is enabled.


.. comp_saf_fmea:: Child requirement
   :id: comp_saf_fmea__child__1
   :safety: QM
   :status: valid
   :mitigated_by: feat_req__parent__QM_invalid
   :expect_not: invalid need(s)

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


.. test_metadata:: Test ID Lenght
   :id: test_metadata__check_id_length
   :partially_verifies_list: LACKS TOOL REQ
   :test_type: requirements_based
   :derivation_technique: requirements_based
   :check: check_id_length

   Tests if the id max lenght check is working as intended



.. Id contains too many characters

.. std_wp:: This is a test
   :id: std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd
   :expect: std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd.id (std_wp__testabcdefghijklmnopqrstuvwxyz123__abcd): exceeds the maximum allowed length of 45 characters (current length: 47).


.. Id has correct length

.. std_wp:: This is a test
   :id: std_wp__test__abce
   :expect_not: exceeds the maximum

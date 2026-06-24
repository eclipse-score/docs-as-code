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


.. test_metadata:: Test ID Format
   :id: test_metadata__check_id_format
   :partially_verifies_list: tool_req__docs_common_attr_id_scheme
   :test_type: requirements_based
   :derivation_technique: requirements_based
   :check: check_id_format

   Tests if the id format is followed.
   3 Part needs, need to follow different conventions than 2 part or undefined part needs


.. Id does not consists of 3 parts

.. stkh_req:: This is a test
   :id: stkh_req__test
   :expect: stkh_req__test.id (stkh_req__test): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.


.. Id consists of 3 parts

.. stkh_req:: This is a test
   :id: stkh_req__test__abcd
   :expect_not: expected to consist of this format


.. Id follows pattern

.. stkh_req:: This is a test
   :id: stkh_req__test__test__abcd
   :expect: stkh_req__test__test__abcd.id (stkh_req__test__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.


.. Id starts with wp and number of parts is 3

.. workproduct:: This is a test
   :id: wp__test__abcd
   :expect: wp__test__abcd.id (wp__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>`.


.. Id is invalid, because it starts with wp and contains 2 parts

.. workproduct:: This is a test
   :id: wp__test
   :expect_not: expected to consist of this format

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
#CHECK: check_id_format

.. Id does not consists of 3 parts
#EXPECT: stkh_req__test.id (stkh_req__test): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. stkh_req:: This is a test
   :id: stkh_req__test

.. Id consists of 3 parts
#EXPECT-NOT: stkh_req__test__abcd.id (stkh_req__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. stkh_req:: This is a test
   :id: stkh_req__test__abcd

.. Id follows pattern
#EXPECT: stkh_req__test__test__abcd.id (stkh_req__test__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. stkh_req:: This is a test
   :id: stkh_req__test__test__abcd

.. Id starts with wp and number of parts is 3
#EXPECT: wp__test__abcd.id (wp__test__abcd): expected to consist of this format: `<Req Type>__<Abbreviations>`.

.. workproduct:: This is a test
   :id: wp__test__abcd

.. Id is invalid, because it starts with wp and contains 2 parts
#EXPECT-NOT: wp__test.id (wp__test): expected to consist of this format: `<Req Type>__<Abbreviations>`.

.. workproduct:: This is a test
   :id: wp__test

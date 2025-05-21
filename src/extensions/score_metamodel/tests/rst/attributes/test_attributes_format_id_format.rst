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
#EXPECT: stk_req__test.id (stk_req__test): expected to consisting of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. stkh_req:: This is a test
   :id: stk_req__test

.. Id follows pattern
#EXPECT-NOT: expected to consisting of this format: `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. std_wp:: This is a test
   :id: std_wp__test__test__abcd

.. Id starts with wp and number of parth is neither 2 nor 3
#EXPECT: wp__test__test__abcd.id (wp__test__test__abcd): expected to consisting of one of these 2 formats:`<Req Type>__<Abbreviations>` or `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. std_wp:: This is a test
   :id: wp__test__test__abcd

.. Id is valid, because it starts with wp and contains 3 parts
#EXPECT-NOT: expected to consisting of one of these 2 formats:`<Req Type>__<Abbreviations>` or `<Req Type>__<Abbreviations>__<Architectural Element>`.

.. std_wp:: This is a test
   :id: wp__test__abce

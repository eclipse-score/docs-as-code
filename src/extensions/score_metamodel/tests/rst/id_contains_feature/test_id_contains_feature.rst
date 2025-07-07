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
#CHECK: id_contains_feature

.. Feature is deeper in the path of the RST file
.. This is now explicitly allowed
#EXPECT-NOT: std_wp__test__abcd.id (std_wp__test__abcd): Feature 'test' not in path

.. std_wp:: This is a test
   :id: std_wp__test__abcd

.. Feature is in the path of the RST file
#EXPECT-NOT: Feature 'id_contains_feature' not in path

.. std_wp:: This is a test
   :id: std_wp__id_contains_feature__abce

.. Check if the feature is in the path of the RST file is skipped,
   because the id contains 4 parts
#EXPECT-NOT: not in path

.. std_wp:: This is a test
   :id: std_wp__test1__test2__abce

.. Check if the feature is in the path of the RST file is skipped,
   because the requirement type is stkh_req
#EXPECT-NOT: Feature 'test' not in path

.. stkh_req:: This is a test
   :id: stkh_req__test__abce

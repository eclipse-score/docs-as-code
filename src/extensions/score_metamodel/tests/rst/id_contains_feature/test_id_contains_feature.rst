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


.. Feature is in the path of the RST file
#EXPECT-NOT[+2]: Feature 'id_contains_feature' not in path

.. std_wp:: This is a test
   :id: std_wp__id_contains_feature__abce


.. Check if the feature is in the path of the RST file is skipped,
   because the id contains 4 parts
#EXPECT-NOT[+2]: not in path

.. std_wp:: This is a test
   :id: std_wp__test1__test2__abce


.. Check if the feature is in the path of the RST file is skipped,
   because the requirement type is stkh_req
#EXPECT-NOT[+2]: Feature 'test' not in path

.. stkh_req:: This is a test
   :id: stkh_req__test__abce



.. Check if feature is correctly found to not be in path
#EXPECT[+2]: Feature part 'abcabc' not found in path 'id_contains_feature'.

.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__abcabc__testing



.. Check if feature is correctly found to be in path
#EXPECT-NOT[+2]: Feature part

.. feat_req:: Testing if warning correctly triggers
   :id: feat_req__id_contains__testing


.. Testing if additional allowed param in conf.py is valid
#EXPECT-NOT[+2]: Feature part

.. feat_req:: Testing conf.py parameter
   :id: feat_req__blabla__testing


.. Testing if additional allowed param in conf.py is valid
#EXPECT[+2]: Feature part 'abcabcabc' not found in path 'id_contains_feature'.

.. feat_req:: Testing conf.py parameter
   :id: feat_req__abcabcabc__blabla_testing

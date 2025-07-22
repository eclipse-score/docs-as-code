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
#CHECK: check_title

.. Title contains a stop word
#EXPECT: feat_req__test__abcd.title (This must work): contains a stop word: `must`.

.. feat_req:: This must work
   :id: feat_req__test__abcd

.. Title contains no stop word
#EXPECT-NOT: feat_req__test__abce.title (This is a test): contains a stop word

.. feat_req:: This is a test
   :id: feat_req__test__abce

.. Title of an architecture element contains a stop word
#EXPECT: logic_arc_int__test__abcd.title (This must work): contains a stop word: `must`.

.. logic_arc_int:: This must work
   :id: logic_arc_int__test__abcd

.. Title of an architecture element contains no stop word
#EXPECT-NOT: logic_arc_int__test__abce.title (This is a test): contains a stop word

.. logic_arc_int:: This is a test
   :id: logic_arc_int__test__abce

.. Title of requirement of type std_wp is not checked for stop words
#EXPECT-NOT: std_wp__test__abce.title (This must work): contains a stop word: `must`.

.. std_wp:: This must work
   :id: std_wp__test__abce

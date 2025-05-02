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
#CHECK: check_options

.. Required option: `status` is missing
#EXPECT: std_wp__test__abcd: is missing required option: `status`.

.. std_wp:: This is a test
   :id: std_wp__test__abcd

.. All required options are present
#EXPECT-NOT: is missing required option

.. std_wp:: This is a test
   :id: std_wp__test__abce
   :status: active

.. Required link `satisfies` refers to wrong requirement type
#EXPECT: feat_req__abce.satisfies (['std_wp__test__abce']): does not follow pattern `^stkh_req__.*$`.

.. feat_req:: Child requirement
   :id: feat_req__abce
   :satisfies: std_wp__test__abce

.. Optional link `supported_by` refers to wrong requirement type
   This check is disabled in check_options.py:114
   #EXPECT: wf__abcd.supported_by (['feat_req__abce']): does not follow pattern `^rl__.*$`.

   .. std_wp:: This is a test
      :id: wf__abcd
      :supported_by: feat_req__abce

.. Optional link `supported_by` refers to the correct requirement type
   This check is disabled in check_options.py:114
   #EXPECT-NOT: does not follow pattern `^rl__.*$`.

   .. std_wp:: This is a test
      :id: wf__abcd
      :supported_by: rl__abcd

   .. rl:: This is a test
      :id: rl__abcd

   .. Required link: `satisfies` is missing
   #EXPECT: feat_req__abcf: is missing required link: `satisfies`.

   .. feat_req:: Child requirement
      :id: feat_req__abcf

.. All required links are present
#EXPECT-NOT: feat_req__abcg: is missing required link

.. feat_req:: Child requirement
   :id: feat_req__abcg
   :satisfies: stkh_req__abcd

.. stkh_req:: Parent requirement
   :id: stkh_req__abcd

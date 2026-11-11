.. *******************************************************************************
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   See the NOTICE file(s) distributed with this work for additional
   information regarding copyright ownership.

   This program and the accompanying materials are made available under the
   terms of the Apache License Version 2.0 which is available at
   https://www.apache.org/licenses/LICENSE-2.0

   SPDX-License-Identifier: Apache-2.0
   *******************************************************************************

Standalone bundle input
=======================

.. Setup: link targets for gd_req satisfies link.

.. workproduct:: Test workproduct
   :id: wp__test_workproduct
   :status: valid
   :version: 1

.. role:: Test role
   :id: rl__test_workflow
   :version: 1

.. workflow:: Test workflow
   :id: wf__test_workflow
   :status: valid
   :version: 1
   :input: wp__test_workproduct
   :output: wp__test_workproduct
   :approved_by: rl__test_workflow
   :responsible: rl__test_workflow

.. gd_req:: Need from a standalone external docs_bundle
   :id: gd_req__external_bundle
   :version: 1
   :satisfies: wf__test_workflow

   The consumer can import Needs from a public ``docs_bundle`` target.

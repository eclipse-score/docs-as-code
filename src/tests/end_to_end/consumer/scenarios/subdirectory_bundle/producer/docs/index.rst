..
   *******************************************************************************
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   See the NOTICE file(s) distributed with this work for additional
   information regarding copyright ownership.

   This program and the accompanying materials are made available under the
   terms of the Apache License Version 2.0 which is available at
   https://www.apache.org/licenses/LICENSE-2.0

   SPDX-License-Identifier: Apache-2.0
   *******************************************************************************

Producer documentation
======================

.. Setup: link targets for gd_req satisfies link.

.. workproduct:: Test workproduct
   :id: wp__test_producer_root
   :status: valid
   :version: 1

.. role:: Test role
   :id: rl__test_producer_root
   :version: 1

.. workflow:: Test workflow
   :id: wf__test_producer_root
   :status: valid
   :version: 1
   :input: wp__test_producer_root
   :output: wp__test_producer_root
   :approved_by: rl__test_producer_root
   :responsible: rl__test_producer_root

.. gd_req:: Producer root requirement
   :id: gd_req__producer_root
   :version: 1
   :satisfies: wf__test_producer_root

   The producer's regular documentation is part of its public docs bundle.

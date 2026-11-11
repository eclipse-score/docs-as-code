..
   *******************************************************************************
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   See the NOTICE file(s) distributed with this work for additional
   information regarding copyright ownership.

   This program and the accompanying materials are made available under the
   terms of the Apache License, Version 2.0 which is available at
   https://www.apache.org/licenses/LICENSE-2.0

   SPDX-License-Identifier: Apache-2.0
   *******************************************************************************

Embedded documentation
======================

.. Setup: link targets for gd_req satisfies link.

.. workproduct:: Test workproduct
   :id: wp__test_embedded
   :status: valid
   :version: 1

.. role:: Test role
   :id: rl__test_embedded
   :version: 1

.. workflow:: Test workflow
   :id: wf__test_embedded
   :status: valid
   :version: 1
   :input: wp__test_embedded
   :output: wp__test_embedded
   :approved_by: rl__test_embedded
   :responsible: rl__test_embedded

.. gd_req:: Embedded requirement
   :id: gd_req__embedded
   :version: 1
   :satisfies: wf__test_embedded

   The embedded documentation is supplied by a docs_bundle in a subdirectory.

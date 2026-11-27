..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
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

Mounted Module
==============

A tool requirement and a testcase of another Bazel module. The report of the
host module must not count them.

.. tool_req:: Mounted capability
   :id: tool_req__mounted_capability
   :version: 1
   :satisfies: gd_req__tool_attr_uid[version==1]

   Belongs to the mounted module.

.. testcase:: Verifies the mounted capability
   :id: testcase__mounted__capability
   :version: 1
   :result: passed
   :fully_verifies: tool_req__mounted_capability

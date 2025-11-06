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

.. Test: No external prefixes (single documentation mega-build)
.. Verifies links work when all needs are loaded in one Sphinx instance, without prefix logic.
#EXPECT-NOT tool_req__test_abcd.satisfies (doc_getstrt__req__process): does not follow pattern `^doc_.+$`.

.. tool_req:: This is a test
   :id: tool_req__test_abcd
   :satisfies: doc_getstrt__req__process

   This should not give a warning


.. Also make sure it works with lists of links

#EXPECT-NOT: tool_req__test_aaaa.satisfies (doc_getstrt__req__process): does not follow pattern `^doc_.+$`.
#EXPECT-NOT: tool_req__test_aaaa.satisfies (gd_guidl__req__engineering): does not follow pattern `^gd_.+$`.

.. tool_req:: This is a test
   :id: tool_req__test_aaaa
   :satisfies: doc_getstrt__req__process;gd_guidl__req__engineering

   This should give a warning

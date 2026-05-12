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

Requirements
============

This repository provides the docs-as-code tooling used by other SCORE
repositories. The pages in this section therefore focus on two questions:

1. Which process requirements are covered by the docs-as-code tooling?
2. How is the tooling itself verified and qualified for downstream use?

Actual product and module traceability is expected to live in consuming
repositories, such as module repositories and integration repositories that use
docs-as-code as a Bazel dependency.

Pages
-----

- ``implementation_state`` describes tooling coverage: implemented capabilities,
  source-code links, test links, full linkage, and process-to-tool mapping.
- ``tooling_verification`` describes verification evidence for the tooling
  itself, including test results and testcase metadata.

.. toctree::
   :maxdepth: 1

   capabilities
   process_overview
   requirements
   implementation_state
   tooling_verification

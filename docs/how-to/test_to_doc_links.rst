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

   # Assisted-by: GitHub Copilot

Reference Docs in Tests
=======================

This guide explains how to annotate test cases so that
docs-as-code automatically creates traceability links between tests and requirements.

The mechanism is language-agnostic:
Bazel produces JUnit-style ``test.xml`` files under ``bazel-testlogs/``.
The ``score_source_code_linker`` extension parses those files, extracts test metadata
(name, file, line, result, and verification properties),
and creates backlinks on the referenced requirements.

Required Properties
-------------------

Every linked test must declare the following properties
(see :need:`gd_guidl__verification_specification`):

``PartiallyVerifies`` *and/or* ``FullyVerifies``
   Comma-separated list of requirement IDs that the test covers.

``TestType``
   For example ``requirements-based``, ``interface-test``, or ``fault-injection``.

``DerivationTechnique``
   For example ``boundary-values``, ``equivalence-classes``, or ``error-guessing``.

``Description``
   A human-readable explanation of the test objective and expected outcome.

If any mandatory property is missing the test will be skipped during link creation.

Language-Specific Annotations
-----------------------------

Each language uses a different mechanism to attach properties to test cases,
but all produce the same JUnit XML output that the linker consumes.

C++ (gTest)
   Use ``RecordProperty`` — shared properties go in ``SetUp()``, per-test properties
   inside each ``TEST_F``.
   See :need:`gd_req__verification_link_tests_cpp`.

Rust
   Use the ``#[record_property]`` attribute macro from the ``test_properties`` crate.
   See :need:`gd_req__verification_link_tests_rust`.

Python (pytest)
   Use the ``@add_test_properties`` decorator; the docstring serves as ``Description``.
   See :need:`gd_req__verification_link_tests_python`.

See :need:`gd_temp__verification_specification` for code templates.

Running Tests and Building Docs
-------------------------------

1. Execute tests so that ``test.xml`` files are generated:

   .. code-block:: bash

      bazel test //...

2. Build the documentation — the linker picks up ``bazel-testlogs/`` automatically:

   .. code-block:: bash

      bazel run //:docs

The resulting documentation shows backlinks on each requirement that is referenced by at least one test.

Limitations
-----------

- Tests must be executed by Bazel before building docs so ``test.xml`` files exist.
- Not compatible with Esbonio / live preview (no ``bazel-testlogs/`` available).
- All mandatory properties must be present; partial metadata causes the test to be silently skipped.

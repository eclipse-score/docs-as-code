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

Reference Docs in Tests
=======================

In tests, you want to reference requirements (needs).
The docs-as-code tool will create backlinks in the documentation.

Docs-as-code parses `test.xml` files produced by Bazel under `bazel-testlogs/`.
To attach metadata to tests use the project tooling decorator (provided by the
attribute plugin). Example usage:

.. code-block:: python

	 from attribute_plugin import add_test_properties

	 @add_test_properties(
			 partially_verifies=["tool_req__docs_common_attr_title", "tool_req__docs_common_attr_description"],
			 test_type="interface-test",
			 derivation_technique="boundary-values",
	 )
	 def test_feature():
			 """Short description of what the test does."""
			 ...

TestLink will extract test name, file, line, result and verification lists
(`PartiallyVerifies`, `FullyVerifies`) and create external needs from tests
and `testlink` attributes on requirements that reference the test.

.. hint::
   It is possible to have 'additional' properties on tests. They will not show up in the
   TestLink but also won't break the parsing process.



Limitations
-----------

- Not compatible with Esbonio/Live_preview.
- To create a valid Testlink Tags and XML must match the expected format.
- Partial properties will lead to no Testlink creation.
  If you want a test to be linked, please ensure all requirement properties are provided.
- Tests must be executed by Bazel first so `test.xml` files exist.


CI/CD Gate for Linkage Percentage
---------------------------------

To enforce traceability in CI:

1. Run tests.
2. Generate ``needs.json``.
3. Execute the traceability checker.

.. code-block:: bash

    bazel test //...
    bazel build //:needs_json
    bazel run //scripts_bazel:traceability_coverage -- \
       --needs-json bazel-bin/needs_json/_build/needs/needs.json \
       --min-req-code 100 \
       --min-req-test 100 \
       --min-req-fully-linked 100 \
       --min-tests-linked 100 \
       --fail-on-broken-test-refs

The checker reports:

- Percentage of implemented requirements with ``source_code_link``
- Percentage of implemented requirements with ``testlink``
- Percentage of implemented requirements with both links (fully linked)
- Percentage of test cases linked to at least one requirement
- Broken testcase references to unknown requirement IDs

To check only unit tests, filter testcase types:

.. code-block:: bash

    bazel run //scripts_bazel:traceability_coverage -- \
  --needs-json bazel-bin/needs_json/_build/needs/needs.json \
       --test-types unit-test

Use lower thresholds during rollout and tighten towards 100% over time.

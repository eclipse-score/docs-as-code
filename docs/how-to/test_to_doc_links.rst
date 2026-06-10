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

Details of implementation
-------------------------

The mechanism is language-agnostic:
The ``score_source_code_linker`` extension parses ``test.xml`` files, extracts test metadata
(name, file, line, result, and verification properties),
and creates backlinks on the referenced requirements.

The extension will look for ``test.xml`` files in both ``bazel-testlogs/``
as well as a folder named ``tests-report/``. This folder can be created manually if the tests
require some pre-run step or are matrix tests or similar.


Required Properties
-------------------

Every linked test must declare the following properties
(see :need:`gd_guidl__verification_specification` for detailed values):

``PartiallyVerifies`` *and/or* ``FullyVerifies``
   Comma-separated list of requirement IDs that the test covers.

``TestType``
   For example ``requirements-based``, ``interface-test``, or ``fault-injection``.

``DerivationTechnique``
   For example ``boundary-values``, ``equivalence-classes``, or ``error-guessing``.

``Description``
   A human-readable explanation of the test objective and expected outcome.
   *In Python tests, a docstring takes the place of the description attribute.*

What should a test.xml look like?
---------------------------------

Each testcase has file as well as it's line number as additional attributes.
Then as described above, each testcase also has properties inside the XML.

.. code-block:: xml

   <?xml version="1.0" encoding="utf-8"?>
   <testsuites name="pytest tests">
     <testsuite errors="0" failures="0" hostname="LG-0005" name="pytest" skipped="0" tests="118" time="6.617" timestamp="2026-06-08T17:56:07.635773+00:00">
       <testcase classname="src.extensions.score_source_code_linker.tests.test_testlink" file="src/extensions/score_source_code_linker/tests/test_testlink.py" line="40" name="test_testlink_serialization_roundtrip" time="0.000">
         <properties>
           <property name="PartiallyVerifies" value="tool_req__docs_test_link_testcase"></property>
           <property name="TestType" value="requirements-based"></property>
           <property name="DerivationTechnique" value="requirements-analysis"></property>
         </properties>
       </testcase>
       <testcase classname="src.extensions.score_source_code_linker.tests.test_testlink" file="src/extensions/score_source_code_linker/tests/test_testlink.py" line="85" name="test_clean_text_removes_ansi_and_html_unescapes" time="0.000">
         <properties>
           <property name="PartiallyVerifies" value="tool_req__docs_test_link_testcase"></property>
           <property name="TestType" value="requirements-based"></property>
           <property name="DerivationTechnique" value="requirements-analysis"></property>
         </properties>
       </testcase>
     </testsuite>
   </testsuites>

If you are not working in Python and using the provided pytest plugin, please ensure that the xml that is written in the end
looks like this, otherwise the extension will not be able to parse the xml correctly.

What happens when properties are missing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When properties or attributes are missing for some or all tests inside the test.xml, testcases are still generated.
However, testcases can only be linked to the requirements if either Partially- or FullyVerifies is filled.

Language-Specific Annotations
-----------------------------

Each language uses a different mechanism to attach properties to test cases,
but all produce the same JUnit XML output that the linker consumes.

C++ (gTest)
   Use ``RecordProperty`` — shared properties go in ``SetUp()``, per-test properties
   inside each ``TEST_F``.
   See :need:`gd_req__verification_link_tests_cpp`.

Rust
   Currently there is no provided official way to do this in Rust.
   We are working with the rust community to figure this out.

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


How do I use the generated testcases?
-------------------------------------

Testcases can be used in different ways inside and outside your documentation.
You can create lists or pie diagrams to showcase all tests as well as statistics on them.
For example you can show all tests like so

.. code-block:: rst

   .. needpie:: Test Results
      :labels: passed, failed, skipped
      :colors: green, red, orange

      type == 'testcase' and result == 'passed'
      type == 'testcase' and result == 'failed'
      type == 'testcase' and result == 'skipped'


.. needpie:: Test Results
   :labels: passed, failed, skipped
   :colors: green, red, orange

   type == 'testcase' and result == 'passed'
   type == 'testcase' and result == 'failed'
   type == 'testcase' and result == 'skipped'

Or show the different types of properties in case you want

.. code-block:: rst

   .. needpie:: Test Types Used In Testcases
      :labels: fault-injection, interface-test, requirements-based, resource-usage
      :legend:

      type == 'testcase' and test_type == 'fault-injection'
      type == 'testcase' and test_type == 'interface-test'
      type == 'testcase' and test_type == 'requirements-based'
      type == 'testcase' and test_type == 'resource-usage'


.. needpie:: Test Types Used In Testcases
   :labels: fault-injection, interface-test, requirements-based, resource-usage
   :legend:

   type == 'testcase' and test_type == 'fault-injection'
   type == 'testcase' and test_type == 'interface-test'
   type == 'testcase' and test_type == 'requirements-based'
   type == 'testcase' and test_type == 'resource-usage'


Limitations
-----------

- Tests must be executed by Bazel before building docs so ``test.xml`` files exist.
- Not compatible with Esbonio / live preview (no ``bazel-testlogs/`` available).

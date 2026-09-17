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

.. _docs_internals_testing:

Testing
=======

docs-as-code verifies itself on several layers.
The following sections describe each testing method,
what it is used for,
and how to run it.

Development checks (pre-commit)
-------------------------------

To be executed before ``git-commit``.

.. code-block:: bash

   uvx pre-commit run --all-files

The hooks cover:

- Generic file hygiene:
  YAML/TOML/JSON validity, trailing whitespace, end-of-file newlines,
  merge-conflict markers, case conflicts, and private keys.
- Python style and linting with Ruff (fix in place).
- Python type checking with BasedPyright.
- GitHub Actions workflow linting with actionlint.
- Bazel module hygiene, including ``bazel mod tidy`` and a lockfile consistency check.
- Eclipse copyright header presence.


Python unit tests (score_pytest)
--------------------------------

The unit tests exercise individual Python functions and extensions
in isolation, without a Sphinx build.

They are defined with the custom ``score_pytest`` Bazel rule,
which wraps pytest and pins a single pytest version for the whole repository.

.. code-block:: bash

   bazel test --lockfile_mode=error //... --build_tests_only

Use this layer for logic inside the extensions,
the helper library,
and the command-line tools.

File-based RST rule checks (metamodel)
--------------------------------------

The file-based tests verify the Sphinx build rules and metamodel checks
including our whole S-CORE-specific Sphinx setup with extensions.
Each RST file under ``src/extensions/score_metamodel/tests/rst/`` is a small,
self-contained Sphinx document with its own ``conf.py``.
A SphinxTestApp builds it and the framework asserts on the resulting warnings,
using the ``:expect:`` / ``:expect_not:`` options on the needs.

You need one target per check category:

.. code-block:: bash

   bazel test //src/extensions/score_metamodel:file_based_tests_<category>

The categories are ``architecture``, ``attributes``, ``graph``,
``id_contains_feature``, ``options``, ``safety``, and ``security``.

Use this layer whenever you change the metamodel (``metamodel.yaml``)
or one of its checks.
How to write such a test file is described in
:doc:`extensions/rst_filebased_testing`.

End-to-end docs.bzl tests (docs_bzl)
------------------------------------

The end-to-end tests exercise the public ``docs()`` and ``docs_bundle()``
macros through real Bazel builds and ``bazel run`` invocations,
exactly like a consumer would use them.
They live under ``src/tests/docs_bzl`` and cover composition,
invalid configurations, external Bzlmod bundles,
and golden HTML/JSON output comparison.

They are not Bazel test targets,
but plain pytest tests that issue Bazel underneath
because these tests also verify our Bazel/Starlark code.

.. code-block:: bash

   .venv_docs/bin/python -m pytest -vv src/tests/docs_bzl

The suite must be run sequentially.
CI splits it with custom markers:
``bazel_cached`` (build-only, fast) and ``bazel_slow``
(Sphinx runs and expected-failure tests).

Use this layer for changes to the Bazel macros,
the bundle composition,
or the generated output format.
It is the "docs-bzl scope" in the diagram above.

Downstream compatibility tests
------------------------------

The downstream compatibility tests check that changes to docs-as-code
do not break real consumer repositories.
They build selected consumers both from a local checkout and from a Git remote,
using the changed docs-as-code as a dependency.

They live under ``src/tests/downstream_compatibility``:

.. code-block:: bash

   .venv_docs/bin/python -m pytest -s src/tests/downstream_compatibility

You can restrict the run to a single consumer with ``--repo``.
In CI they run on demand, triggered by a ``/consumer-test`` comment on a PR.

How CI orchestrates the layers
------------------------------

The PR workflow (``.github/workflows/_test.yml``) runs, in order:

1. the pre-commit development checks,
2. the ``docs_bzl`` end-to-end tests (``bazel_cached`` then ``bazel_slow``),
3. ``bazel test --lockfile_mode=error //... --build_tests_only``
   (all unit and file-based tests),
4. ``bazel build --lockfile_mode=error //...``,
   skipping the test directories because some contain non-buildable
   negative test scenarios.

The downstream compatibility tests run only on request,
and the link check runs nightly.
The documentation itself is rebuilt from the merged state afterwards.

Which test for what
-------------------

Use the first suitable one in the table below.
The later tests are slower.

.. list-table::
   :widths: 45 55
   :header-rows: 1

   * - Change
     - Relevant layer
   * - Any change
     - Development checks (pre-commit)
   * - Python logic in extensions / helper library / CLI
     - Unit tests (``bazel test //...``)
   * - Metamodel or its checks
     - File-based RST rule checks
   * - Bazel macros, bundles, or output format
     - End-to-end docs_bzl tests
   * - Public API, layouts, or version requirements
     - Downstream compatibility tests
   * - Links or external references in the docs
     - Documentation link checks

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

Setup
=====

docs-as-code enables you to integrate Sphinx documentation generation into a
Bazel build system.
It contains utilities and extensions that improve documentation in S-CORE.

1. MODULE.bazel file
--------------------

Add the module to the ``MODULE.bazel`` file::

    bazel_dep(name = "score_docs_as_code", version = "7.0.0")

Add the S-CORE Bazel registry to the ``.bazelrc`` file::

    common --registry=https://raw.githubusercontent.com/eclipse-score/bazel_registry/main/
    common --registry=https://bcr.bazel.build

2. Diagram tools
----------------

Bazel downloads a native `PlantUML <https://www.plantuml.com>`_ distribution
for the platform running Sphinx. PlantUML does not require a separate Java
installation. Supported platforms are Linux x86-64, Linux ARM64 and macOS ARM64.

Install `Graphviz <https://graphviz.org/download/>`_ and make its ``dot``
executable available on ``PATH`` for diagrams that require Graphviz layout.

3. BUILD file
-------------

.. code-block:: starlark

    load("@score_docs_as_code//:docs.bzl", "docs")

    docs(
        project = "S-CORE <feature name>",
        project_url = "https://eclipse-score.github.io/<repo name>",
        external_needs = [
            "@other_repo//:docs",  # Optional, if you reference another project's Needs
        ],
    )

For configuration options, see :ref:`docs_bazel-macros`.

4. Run a documentation build
----------------------------

.. code-block:: bash

    bazel run //:docs

Access your documentation at ``/_build/index.html``.

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

2. .bazelrc file
----------------

The system uses `PlantUML <https://www.plantuml.com>`_ for diagrams. This action
requires Java.
If the system does not contain Java, Bazel downloads a remote JDK
from the network.
This action requires configuration in the ``.bazelrc`` file::

    build --java_language_version=17
    build --java_runtime_version=remotejdk_17
    build --tool_java_language_version=17
    build --tool_java_runtime_version=remotejdk_17

3. BUILD file
-------------

.. code-block:: starlark

    load("@score_docs_as_code//:docs.bzl", "docs")

    docs(
        project = "S-CORE <feature name>",
        project_url = "https://eclipse-score.github.io/<repo name>",
        external_needs = [
            "@other_repo:needs_json",  # Optional, if you have dependencies
        ],
    )

For configuration options, see :ref:`docs_bazel-macros`.

4. Run a documentation build
----------------------------

.. code-block:: bash

    bazel run //:docs

Access your documentation at ``/_build/index.html``.

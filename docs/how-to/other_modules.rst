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

Reference Other Modules
=======================

This document explains how to enable cross-module (bi-directional) linking between documentation modules with Sphinx-Needs in this project.
In short:

1. Make the other module available to Bazel via the `MODULE` (aka `MODULE.bazel`) file.
2. Choose one integration mode: import its built ``needs.json`` **or** mount its
   documentation sources.
3. Reference Needs using the normal Sphinx-Needs referencing syntax.

Details and Example
-------------------

1) Include the other module in `MODULE.bazel`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The consumer module must declare the other modules as dependencies in the `MODULE.bazel` file so Bazel can fetch them.
There are multiple ways to do this depending on how you manage third-party/local modules (git, local overrides, etc.).

A minimal example (add or extend the existing `bazel_deps` stanza):

.. code-block:: starlark

	 bazel_dep(name = "score_process_description", version = "2.1.0")

2a) Import the other module's built inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation build is exposed via a Bazel macro that accepts an ``external_needs`` parameter
for external ``:needs_json_file`` targets.
Use ``external_needs`` instead of ``data`` when the target produces needs JSON —
``data`` is meant for non-needs runfiles (e.g. custom tool outputs).

Example `BUILD` snippet (consumer module):

.. code-block:: starlark

    load("@score_docs_as_code//:docs.bzl", "docs")
    docs(
      external_needs = [
         "@score_process_description//:needs_json",
      ],
      source_dir = "docs",
    )


2b) Mount the external module's documentation bundle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation build in this project is exposed via a Bazel macro that accepts
a ``bundles`` parameter. Mount the external module's auto-exposed
``:docs_bundle`` bundle. The mounted sources define their needs in the host
build, so do **not** also add that module's ``:needs_json`` to ``data`` — doing
so would create duplicate need IDs.

Example `BUILD` snippet (consumer module):

.. code-block:: starlark

    load("@score_docs_as_code//:docs.bzl", "docs")
    docs(
      bundles = [
          {
              "bundle": "@score_process_description//:docs_bundle",
              "mount_at": "process",
              "attach_to": "index",
          },
      ],
      source_dir = "docs",
    )

See :ref:`howto_mount_external_sources` for the full mount reference, and
:ref:`docs_bidirectional_traceability` for more on cross-module linking.

3) Reference needs across modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the other module's are defined as dependencies as explained above, you can reference their needs IDs in the usual Sphinx-Needs way.
The important part is that the inventory name that Sphinx-Needs looks up matches the module that produced the needs entries.

Example in reStructuredText:

.. code-block:: rst

	See the requirement :need:`gd_req__req_traceability`, for example.

Which results in:

   See the requirement :need:`gd_req__req_traceability`, for example.

See the `Sphinx-Needs documentation <https://sphinx-needs.readthedocs.io/en/latest/>`_
for more details on cross-referencing needs.

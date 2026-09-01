..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

Bundle examples
===============

This page is a catalog of focused bundle patterns. Start with
:doc:`index` for the basic workflow; use these examples when documentation is
split across bundles, generated during the build, or published by another
Bazel module. Each example shows the bundle declaration, its placement in the
consuming project, and the resulting location in the documentation output.

Nest bundles
------------

Use nested bundles when one bundle contains another. The child bundle chooses
its entry page, the parent chooses the child's relative location, and the
consuming project chooses where the assembled bundle appears.

The tested parent bundle composes the child like this:

.. code-block:: starlark

   docs_bundle(
       name = "parent",
       source_dir = "parent",
       bundles = [{
           "bundle": ":child",
           "mount_at": "child",
       }],
       data = [":generated_doc_output"],
       visibility = ["//visibility:public"],
   )

See the `complete nested-bundles fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/nested_bundles>`_.

If the parent is mounted at ``guides/example``, its page is rendered at
``guides/example/index.html`` and the child landing page at
``guides/example/child/landing.html``. The consuming project can change
``guides/example`` without changing either bundle.

Mount generated documentation
-----------------------------

When a build action produces documentation rather than a source-tree ``.rst``
file, create a bundle without ``source_dir``. Its generated files are the
bundle's complete payload. You can generate and mount a page like this:

.. code-block:: starlark

   genrule(
       name = "generated_page",
       srcs = [],
       outs = ["generated/index.rst"],
       cmd = """echo 'Generated Data Page
   ===================' > $@""",
   )

   # Pure-data bundle: the genrule output lives in ``bazel-out/``, not the tree.
   docs_bundle(
       name = "data_bundle",
       data = [":generated_page"],
       entry_doc = "index",
       visibility = ["//visibility:public"],
   )

   docs(
       source_dir = "docs",
       bundles = [{
           "bundle": ":data_bundle",
           "mount_at": "data_test",
           "attach_to": "index",
       }],
   )

See the `complete generated-data fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/data_files_runfiles>`_.

The generated page is rendered at ``data_test/index.html`` and is added to the
consuming project's index page's toctree. It is mounted and navigated in
exactly the same way as a bundle with source files.

Mount documentation from another module
----------------------------------------

Every project using ``docs()`` exposes its own documentation as a
``:docs_bundle`` target. The external-bundle test fixture mounts that target
like this:

.. code-block:: starlark

   docs(
       source_dir = "host_docs",
       test_sources = ["src/tests/docs_bzl/scenarios/external_bundle"],
       bundles = [{
           "bundle": "@score_process_description//:docs_bundle",
           "mount_at": "process",
       }],
   )

See the `complete external-bundle fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/external_bundle>`_.

The external bundle's entry page is rendered at ``process/index.html`` and is
added to the consuming project's index by ``attach_to``. Mounted sources also
bring their Need directives with them, so do not import the same module's
``needs_json`` separately.

.. seealso::

   :ref:`howto_mount_external_sources` for the full mount reference and
   :ref:`docs_bazel-macros` for the ``docs`` and ``docs_bundle`` attributes.

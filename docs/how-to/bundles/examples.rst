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

Mount generated bundle content
------------------------------

Use explicit ``srcs`` when a build action produces the documentation rather
than a source-tree ``.rst`` file. The source-less bundle has no ``source_dir``;
its generated files are the bundle's complete source payload. You can generate
and mount a page like this:

.. code-block:: starlark

   genrule(
       name = "generated_page",
       srcs = [],
       outs = ["generated/index.rst"],
       cmd = """echo 'Generated Data Page
   ===================' > $@""",
   )

   # Source bundle: the genrule output lives in ``bazel-out/``, not the tree.
   docs_bundle(
       name = "data_bundle",
       srcs = [":generated_page"],
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
consuming project's index page's toctree. A generated source bundle is mounted
and navigated in exactly the same way as a bundle with workspace sources.

.. _howto_docs_assets:

Ship pre-built files (Doxygen HTML, PDFs, images)
-------------------------------------------------

Use ``docs_assets`` for files that are already finished and must appear in the
HTML site unchanged: Doxygen output, PDFs, images, or any other file type.
Sphinx never reads these files; they are copied into the output after the
build.

.. code-block:: starlark

   load("@score_docs_as_code//:docs.bzl", "docs", "docs_assets")

   docs_assets(
       name = "api_docs",
       srcs = [
           ":doxygen_html",  # a directory output, for example from a Doxygen rule
           "manual.pdf",  # any file
       ],
   )

   docs(
       source_dir = "docs",
       bundles = [{
           "bundle": ":api_docs",
           "mount_at": "api",
       }],
   )

This produces:

* ``api/index.html`` and the rest of the Doxygen tree, because a directory's
  *contents* go to ``mount_at``;
* ``api/manual.pdf``, because a file goes to ``<mount_at>/<file name>``.

Assets get no toctree entry. Link to them from a normal page instead, for
example in ``docs/index.rst``:

.. code-block:: rst

   * `API reference <api/index.html>`_
   * `User manual <api/manual.pdf>`_

A ``docs_assets`` target is placed like any other bundle, so it can also sit
inside a child bundle: mounted at ``api`` in a bundle that is mounted at
``child``, the files land in ``child/api/``. See the `complete docs-assets
fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/docs_assets>`_,
which mounts an HTML directory, a PDF, a PNG, and an SVG this way.

``data`` or ``docs_assets``?

* ``docs_bundle(data = [...])``: Sphinx reads or references the file, for
  example an image used by an ``.. image::`` directive.
* ``docs_assets``: the file is copied as-is and Sphinx never sees it.

Assets are copied only by the HTML builds (``bazel run //:docs`` and
``live_preview``). ``needs_json``, ``docs_check``, and ``docs_link_check`` never
build them, so a slow Doxygen run does not slow down those targets.

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

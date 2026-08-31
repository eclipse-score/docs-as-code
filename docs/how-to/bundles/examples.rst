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

.. literalinclude:: examples/nested_bundles.inc
   :language: starlark
   :start-after: BEGIN docs-bundle-howto: parent-composition
   :end-before: END docs-bundle-howto: parent-composition

See the `complete nested-bundles fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/nested_bundles>`_.

If the parent is mounted at ``guides/example``, its page is rendered at
``guides/example/index.html`` and the child landing page at
``guides/example/child/landing.html``. The consuming project can change
``guides/example`` without changing either bundle.

Mount generated documentation
-----------------------------

Use a data-only bundle when a build action produces the documentation rather
than a source-tree ``.rst`` file. It has no ``source_dir``; its generated files
are the bundle's complete payload. You can generate and mount a page like this:

.. literalinclude:: examples/generated_data.inc
   :language: starlark
   :start-after: BEGIN docs-bundle-howto: generated-data
   :end-before: END docs-bundle-howto: generated-data

See the `complete generated-data fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/data_files_runfiles>`_.

The generated page is rendered at ``data_test/index.html`` and is added to the
consuming project's index page's toctree. Although this bundle is data-only,
it is mounted and navigated in exactly the same way as a bundle with source
files.

Mount documentation from another module
----------------------------------------

Every project using ``docs()`` exposes its own documentation as a
``:docs_bundle`` target. The external-bundle test fixture mounts that target
like this:

.. literalinclude:: examples/external_bundle.inc
   :language: starlark
   :start-after: BEGIN docs-bundle-howto: external-bundle
   :end-before: END docs-bundle-howto: external-bundle

See the `complete external-bundle fixture on GitHub
<https://github.com/eclipse-score/docs-as-code/tree/main/src/tests/docs_bzl/scenarios/external_bundle>`_.

The external bundle's entry page is rendered at ``process/index.html`` and is
added to the consuming project's index by ``attach_to``. Mounted sources also
bring their Need directives with them, so do not import the same module's
``needs_json`` separately.

.. seealso::

   :ref:`howto_mount_external_sources` for the full mount reference and
   :ref:`docs_bazel-macros` for the ``docs`` and ``docs_bundle`` attributes.

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

.. _howto_mount_external_sources:

How to use bundles
==================

This page is the getting-started guide for documentation bundles: define a
bundle, mount it in a project, compose it with other bundles, and consume a
bundle from another module. For focused patterns and test-backed examples,
see :doc:`examples`.

Declare a bundle
----------------

Create a ``docs_bundle`` next to the source directory that it exports:

.. code-block:: starlark

   # src/BUILD
   load("//:docs.bzl", "docs_bundle")

   docs_bundle(
       name = "docs_dir",
       source_dir = "docs",
       visibility = ["//visibility:public"],
   )

``source_dir`` is the root of the mounted tree. Its supported documentation
files are collected like those of ``docs()``; for example,
``src/docs/overview.rst`` becomes ``overview`` within the bundle.
``entry_doc`` names the bundle-relative page used for navigation when the
bundle is mounted.

Mount a bundle in a project
---------------------------

Pass a placement dictionary to ``docs(bundles = [...])``:

.. code-block:: starlark

   load("//:docs.bzl", "docs")

   docs(
       bundles = [
           {
               "bundle": "//src:docs_dir",
               "mount_at": "internals/code_docs",
           },
       ],
       source_dir = "docs",
   )

``bundle`` identifies the ``docs_bundle`` target and ``mount_at`` selects the
docname prefix in this project. In this example, ``overview.rst`` is available
as ``internals/code_docs/overview``.

Every mount adds the bundle's configured entry document to a host toctree. By
default that is the ``index`` beside ``mount_at``; ``attach_to`` overrides the
host document whose first toctree receives the entry. The entry itself belongs
to the ``docs_bundle`` and defaults to ``index``.

The configuration has two separate responsibilities:

.. plantuml::

   @startuml
   left to right direction
   rectangle "docs_bundle\ncontent" as bundle
   rectangle "docs(bundles = [...])\nplacement" as docs
   rectangle "Rendered docs" as output
   bundle --> docs : select bundle
   docs --> output : mount_at / attach_to
   @enduml

For nested composition, generated bundle data, and bundles published by
another Bazel module, see :doc:`examples`.

Refresh the generated project configuration
-------------------------------------------

After changing ``bundles``, run either command once:

.. code-block:: console

   $ bazel run //:docs
   $ bazel run //:docs_check

Both commands refresh the repository-root ``ubproject.toml`` used by IDE tools.
``bazel build //:needs_json`` checks the sandboxed needs build without creating
that developer-facing file.

Further Examples
----------------

The :doc:`examples` page shows nested composition, generated bundle data, and
the declaration for a bundle exported by another Bazel module.

.. toctree::
   :maxdepth: 1
   :hidden:

   examples

Further reading
---------------

* :ref:`docs_concept_mounts` — bundle and mount semantics.
* `sphinx-mounts documentation <https://sphinx-mounts.useblocks.com/>`_ — the underlying mechanism.

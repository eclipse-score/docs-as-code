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

Mount docs bundles
==================

Use a documentation bundle to publish RST or Markdown that lives outside a
project's ``docs/`` directory. For the terminology and composition rules, see
:ref:`docs_concept_mounts`.

.. contents::
   :local:
   :depth: 2

Declare a bundle
----------------

Create a ``docs_bundle`` next to the source directory that it exports:

.. code-block:: starlark

   # src/BUILD
   load("//:docs.bzl", "docs_bundle")

   docs_bundle(
       name = "docs_dir",
       source_dir = "docs",
       entry_doc = "overview",  # default: "index"
       visibility = ["//visibility:public"],
   )

``source_dir`` is the root of the mounted tree. Its supported documentation
files are collected like those of ``docs()``; for example,
``src/docs/index.rst`` becomes ``index`` within the bundle.
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
               "attach_to": "internals/index",
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

Compose bundles
---------------

A bundle can include other bundles. The child placement is relative to the
parent bundle, and the consumer chooses where the assembled bundle appears:

.. code-block:: starlark

   docs_bundle(
       name = "guide",
       source_dir = "guide",
       bundles = [
           {
               "bundle": "//some/pkg:api_docs",
               "mount_at": "reference",
               "attach_to": "index",
           },
       ],
   )

Mounting ``guide`` at ``internals/code_docs`` makes the child available below
``internals/code_docs/reference``. A build fails if the same bundle would end
up at two different final locations.

Mount a bundle from another Bazel module
----------------------------------------

Every project using ``docs()`` exposes its own source directory as
``:docs_bundle``. Mount such a bundle from another module by using its label:

.. code-block:: starlark

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

Mounted sources bring their Need directives with them. Do not also add that
module's ``:needs_json`` target to ``data``: Sphinx-Needs would receive each
Need twice. Use ``:needs_json`` only for a dependency whose documentation is
not mounted.

An external module's mounted sources are staged by Bazel, so navigation leads
to a read-only staged tree. Mount every external module explicitly; bundles do
not automatically re-export mounts from other external modules.

Refresh the generated project configuration
-------------------------------------------

After changing ``bundles``, run either command once:

.. code-block:: console

   $ bazel run //:docs
   $ bazel run //:docs_check

Both commands refresh the repository-root ``ubproject.toml`` used by IDE tools.
``bazel build //:needs_json`` checks the sandboxed needs build without creating
that developer-facing file.

Further reading
---------------

* :ref:`docs_concept_mounts` — bundle and mount semantics.
* `sphinx-mounts documentation <https://sphinx-mounts.useblocks.com/>`_ — full
  configuration reference.

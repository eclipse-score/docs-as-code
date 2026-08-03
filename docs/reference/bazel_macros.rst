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
.. _docs_bazel-macros:

Bazel macro: ``docs``
=====================

The ``docs`` macro defined in ``docs.bzl`` is a convenience wrapper
that creates a small set of Bazel targets
to build, verify and preview the project's Sphinx documentation,
and to create a Python virtual environment for IDE support (Esbonio).

See :doc:`commands <commands>` for the targets/commands it creates.

The macro must be called from the repository root package.

Minimal example (root ``BUILD``)
--------------------------------

.. code-block:: python

   load("//:docs.bzl", "docs")

   docs(
       source_dir = "docs",
       data = [
           # labels to any extra tools or data you want included
           # e.g. "//:needs_json" or other tool targets
       ],
       bundles = [
           # dicts describing bundles to mount into this project
           # e.g. {"bundle": "@score_process//:docs_bundle", "mount_at": "process"}
       ],
       deps = [
           # additional bazel labels providing Python deps or other runfiles
       ],
   )

- ``source_dir`` (string, default: ``"docs"``)
  Path (relative to repository root) to your Sphinx source directory. This is the folder
  that contains your ``conf.py`` and the top-level ReST/markdown sources.

- ``data`` (list of bazel labels)
  Extra runfiles / data targets that should be made available to the documentation targets.
  The items in ``data`` are added to the py_binaries and to the Sphinx tooling so they are
  available at build time.

  .. note::

     To pull in another module's needs for cross-referencing, add its
     ``:needs_json`` target here.

- ``bundles`` (list of placement dicts)
  Documentation bundles to overlay into this project's documentation tree, each with its
  placement (``mount_at``). See :ref:`howto_mount_external_sources` for the full reference.

- ``deps`` (list of bazel labels)
  Additional Bazel dependencies to add to the Python binaries and the virtual environment
  target. Use this to add project-specific Python modules.

  If you don't provide the necessary Sphinx packages,
  this function adds its own (but checks for conflicts).

- ``scan_code`` (list of bazel labels)
  Source code targets to scan for traceability tags (``req-Id:`` annotations).
  Used to generate the source-code-link JSON that maps tags back to source files.

- ``metamodel`` (bazel label, optional)
  Path to a custom ``metamodel.yaml`` file.
  When set, the ``score_metamodel`` extension loads **this file instead of** the default metamodel.
  The label is automatically added to the ``data`` and ``tools`` of every generated target
  so the file is available in the Bazel sandbox at build time.

  Example:

  .. code-block:: python

     docs(
         source_dir = "docs",
         metamodel = "//:my_metamodel.yaml",
     )

  The custom ``metamodel.yaml`` must follow the same schema as the default one
  (see :ref:`score_metamodel <metamodel>`).
  You may use ``@score_docs_as_code//src/extensions/score_metamodel:metamodel_yaml``
  for extension processing.
  When ``metamodel`` is omitted the default metamodel is used unchanged.

.. _docs_bundle_macro:

Bazel macro: ``docs_bundle``
----------------------------

``docs_bundle`` (also from ``docs.bzl``) declares a **mountable documentation
bundle**: a chunk of RST/Markdown content that can be overlaid into a host
documentation project. A bundle carries only *content* — it has **no placement of its
own**. Where it appears is decided by whoever mounts it (a composing
``docs_bundle`` or the :ref:`docs(bundles=[...]) <howto_mount_external_sources>` call
site).

.. code-block:: python

   load("//:docs.bzl", "docs_bundle")

   docs_bundle(
       name = "docs_dir",
       source_dir = "docs",
       entry_doc = "index",
       bundles = [],
       visibility = ["//visibility:public"],
   )

Signature: ``docs_bundle(name, source_dir = None, entry_doc = "index", bundles = [], scan_code = [], tests = [], visibility = None)``.

- ``source_dir`` (string, optional)
  Directory holding the bundle's own doc sources. It is globbed the same way as
  ``docs()`` (RST, Markdown, images, and the other doc file kinds). The
  ``source_dir`` itself is the mount root, so the files mount relative to it (so
  ``concept/index.rst`` with ``source_dir = "concept"`` becomes ``index.rst``).
  The bundle exposes those files as a Bazel depset (via the ``DocsBundleInfo``
  provider) and records the ``source_dir`` path; sphinx-mounts walks that original
  directory directly — no copy is made. Leave it unset for a pure aggregator that only
  composes ``bundles``.

- ``entry_doc`` (string, optional)
  Bundle-relative docname used as the canonical navigation entry. It defaults to
  ``index``. Every mount attaches this entry to the parent ``index`` toctree by
  default; a placement's ``attach_to`` may override that host document.

- ``bundles`` (list of composition dicts, optional)
  Nested bundles to compose into this one, so a bundle can aggregate other
  bundles transitively. Each entry is a dict:

  - ``bundle`` — label of another ``docs_bundle`` target.
  - ``mount_at`` — the docname prefix at which the child bundle appears *inside*
    this bundle.
  - ``attach_to`` (optional) — a docname (relative to this bundle) whose toctree
    receives the child's bundle-defined entry document. When omitted, the parent
    ``index`` document receives it.

  A child's ``mount_at``/``attach_to`` **prefix-stack** with the placement this
  bundle later receives, so composition is fully transitive. The same underlying
  bundle resolving to two different final ``mount_at`` values is a hard build
  error. See :ref:`howto_mount_external_sources` for a worked example and
  :ref:`docs_concept_mounts` for the composition and transitivity semantics.

.. note::

   A bundle is **placement-free**: its ``mount_at`` and ``attach_to`` are assigned
   by the mounter, while its ``entry_doc`` belongs to the bundle. This lets the
   same bundle be mounted at different locations by different consumers without
   changing its canonical entry page.

- ``tests`` (list of Bazel labels, optional)
   Executable test targets verified by the automatically created
   ``<name>_tests`` target. Run it with ``bazel test :<name>_tests``. Test
   targets must create non-empty JUnit XML at the path in
   ``XML_OUTPUT_FILE``. The test runner is transitively composed with nested
   bundles, but it is separate from the documentation build and does not make
   documentation targets ``testonly``.

Edge cases
----------

- If your Sphinx ``conf.py`` expects files generated by other Bazel targets, make sure those
  targets are included in the ``data`` list so they are available to the build driver.

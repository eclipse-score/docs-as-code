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

Bundle content and supporting files
-----------------------------------

There are two ways to add files to a bundle. The ``data`` argument of ``docs()``
is shorthand for supporting files in the root ``:docs_bundle``:

* ``docs_bundle(srcs = [...])`` puts documentation source files in a bundle.
  The files may be generated outputs from another build action; they are
  processed as documentation sources and resolved below the bundle's eventual
  ``mount_at`` path.
* ``docs_bundle(data = [...])`` puts supporting or runtime files in a bundle
  payload. Use this for files that belong at the mount but are not themselves
  documentation sources.
* ``docs(data = [...])`` puts supporting files in the root ``:docs_bundle``
  exposed by ``docs()``. A mounted module puts its files in its own bundle;
  these files travel with that bundle and are resolved below its eventual
  ``mount_at`` path.

If a file is mounted documentation, use ``docs_bundle(srcs = [...])``. Both
bundle attributes make files available to a build; they differ in whether the
files are processed as documentation sources or carried as supporting data.

Minimal example (root ``BUILD``)
--------------------------------

.. code-block:: python

   load("//:docs.bzl", "docs")

   docs(
       source_dir = "docs",
       project = "My Project",
       project_url = "https://github.com/eclipse-score/my-project",
       data = [
           # labels to any extra tools or data you want included
           # e.g. "//:needs_json" or other tool targets
       ],
       bundles = [
           # dicts describing bundles to mount into this project
           # e.g. {"bundle": "@score_process_description//:docs_bundle", "mount_at": "process"}
       ],
       deps = [
           # additional bazel labels providing Python deps or other runfiles
       ],
   )

- ``source_dir`` (string, default: ``"docs"``)
  Path (relative to repository root) to your Sphinx source directory. This is the folder
  that contains the top-level ReST/markdown sources. A ``conf.py`` is optional.

- ``project`` and ``project_url`` (strings, optional)
  Project name and canonical project URL. They are required when ``source_dir``
  has no ``conf.py``; in that case ``docs()`` generates the Sphinx configuration
  and supplies the Docs-as-Code baseline version, extensions, and a
  ``required_in_id`` entry derived from the Bazel module name. The first
  underscore-separated prefix is removed (for example,
  ``score_docs_as_code`` becomes ``docs_as_code``). If a ``conf.py`` exists,
  it remains authoritative and these values are not used.

- ``data`` (list of bazel labels)
  Supporting files for this project's root ``:docs_bundle``. The files are
  available to the documentation targets and travel when another project
  mounts this project's public bundle. Put files belonging to a mounted child
  in that child's ``docs_bundle(data = [...])`` instead.

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

- ``code_targets`` (list of Bazel labels)
  Implementation targets or filegroups to scan for traceability tags
  (``req-Id:`` annotations). Implementation target ``srcs``, ``hdrs``, and
  ``textual_hdrs`` are collected through their ``deps`` recursively; filegroups
  expand to their files. Each documentation bundle produces one cache for its
  declared targets; Bazel reuses that cache while its inputs are unchanged. The
  generated JSON is supplied to ``live_preview`` just like a normal documentation
  build.

- ``external_needs`` (list of bazel labels)
  External ``:needs_json_file`` targets from other modules/repositories
  for referencing their needs.
  Do not use ``:needs_json`` targets.

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

Signature: ``docs_bundle(name, source_dir = None, srcs = [], data = [], entry_doc = "index", bundles = [], code_targets = [], visibility = None)``.

- ``source_dir`` (string, optional)
  Directory holding the bundle's own doc sources. It is globbed the same way as
  ``docs()`` (RST, Markdown, images, and the other doc file kinds). The
  ``source_dir`` itself is the mount root, so the files mount relative to it (so
  ``concept/index.rst`` with ``source_dir = "concept"`` becomes ``index.rst``).
  Standalone bundle-local Needs exports always use a self-contained, generated
  Sphinx configuration. A root bundle created by ``docs()`` instead uses the
  project's ``conf.py`` so its local export matches the normal project build.
  The bundle exposes those files as a Bazel depset (via the ``DocsBundleInfo``
  provider) and records the ``source_dir`` path; sphinx-mounts walks that original
  directory directly — no copy is made. Leave it unset for a bundle whose
  sources are supplied explicitly or for an aggregator that only composes
  other ``bundles``.

- ``srcs`` (list of bazel labels, optional)
  Explicit documentation source files, including generated outputs from a
  build action. Use this for a source-less bundle whose documentation is
  generated. All files must share one parent directory. It cannot be combined
  with ``source_dir``.

- ``data`` (list of bazel labels, optional)
  Supporting or runtime files owned by this bundle. These files are part of the
  bundle payload and are available at the bundle's eventual mount path, but are
  not processed as the bundle's documentation sources. Use ``docs(data = [...])``
  for supporting files in the root bundle and this attribute for child bundles.

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

- ``needs_local`` (internal target)
  A source-bearing bundle creates ``<name>.__internal__.needs_local`` with the
  Needs declared by its own sources. The standalone build is intentionally
  self-contained in this version: references to Needs defined outside the
  bundle remain unresolved and fail strict builds. Cross-bundle imports and
  merged exports are planned for a later change. Data-only bundles do not
  create a Needs target.

.. note::

   A bundle is **placement-free**: its ``mount_at`` and ``attach_to`` are assigned
   by the mounter, while its ``entry_doc`` belongs to the bundle. This lets the
   same bundle be mounted at different locations by different consumers without
   changing its canonical entry page.

- ``code_targets`` (list of Bazel labels, optional)
   Implementation targets or filegroups to scan for requirement tags.
   Implementation target ``srcs``, ``hdrs``, and ``textual_hdrs`` are collected
   recursively from their ``deps``; filegroups expand to their files. The bundle
   owns one cached scan result; Bazel only regenerates it when its collected source
   inputs change.

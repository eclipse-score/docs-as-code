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

.. _mount_external_sources:

Mounting external source bundles
================================

This guide explains how to surface RST or Markdown content that lives
**outside** ``docs/`` into the Sphinx build, without copying or
symlinking. It also covers why the underlying ``sphinx-mounts``
extension was introduced and how it compares to alternative
"materialize-a-tree" approaches.

.. contents::
   :local:
   :depth: 2


The problem
-----------

The S-CORE documentation toolchain has historically assumed that every
RST/Markdown file under a Sphinx project lives under its source
directory (``docs/`` in this repository). Two situations break that
assumption:

* **Generated content** — RST produced by a Bazel rule lands under
  ``bazel-bin/...`` and is therefore outside ``docs/`` by construction.
  Examples: API reference tables generated from code, requirement
  catalogues exported from upstream modules, traceability matrices.

* **In-repo content owned by another tree** — for example, README-style
  documentation that lives next to its source code under ``src/`` and
  must remain there for code-ownership reasons but should still appear
  in the rendered docs site.

Historical workarounds either (a) copied or symlinked the files into
``docs/`` — which loses the original source location for IDE
navigation, complicates ``git blame``, and risks stale copies — or
(b) materialized an entire merged source tree at build time and
pointed Sphinx at that. The latter solves the build-side problem but
keeps Sphinx on the IDE critical path. Useful editing in an IDE
requires validation **as you type**, and that is hard to achieve from
any tool without live knowledge of every file and dependency in the
project. Sphinx is built for batch document processing, not for the
millisecond-latency feedback an editor needs; routing IDE feedback
through it therefore caps the editing experience at the speed and
scope of the next rebuild.


What ``sphinx-mounts`` does
---------------------------

`sphinx-mounts`_ is a Sphinx extension that registers external source
trees with Sphinx's project map by **absolute path**, without copying
or staging. The original files stay exactly where they live; Sphinx
reads them from there. Configuration is declarative TOML in
``ubproject.toml``, the file already shared with Sphinx-Needs,
sphinx-codelinks, and ubCode.

.. _sphinx-mounts: https://sphinx-mounts.useblocks.com/

The key consequence: **every consumer reads the same file**. ubCode,
language servers, indexers, and CI gates can all parse
``ubproject.toml`` to discover where a project's RST sources live —
including the mounted ones — without ever invoking Sphinx. That
preserves the IDE editing experience (real-time validation, jump-to-
definition pointing at the real source, schema-aware autocomplete)
while still letting Sphinx produce the published HTML.


Why this matters for IDE support
--------------------------------

ubCode (and similar tooling) walks **up** the directory tree from an
open ``.rst`` / ``.md`` file to find the nearest ``ubproject.toml``,
treats that directory as the project root, and reads the file to
learn the type system, link types, layouts, and field defaults the
project uses. For files inside ``docs/``, the host's
``docs/ubproject.toml`` is found naturally. For files inside a
**mounted** bundle (for example, ``src/docs/overview.rst``), the
walk-up never crosses into ``docs/``, so the host's TOML is invisible.

To close this gap, the ``docs()`` macro also generates a *bundle*
``ubproject.toml`` at each in-repo bundle's source root. The bundle
TOML is a sanitized copy of the host's: it preserves the type
system, link types, layouts, fields, and parse extensions but drops
path-bound entries (external needs JSON paths, ``[[mounts]]``,
schema-path settings) that would otherwise create dead links from
the bundle's location. The result is self-contained TOML that ubCode
can read no matter where the user opens a file from.


Comparison with the materialization approach
--------------------------------------------

+---------------------------------------+---------------------------------------+---------------------------------------+
| Concern                               | Materialize-then-Sphinx               | sphinx-mounts (this approach)         |
+=======================================+=======================================+=======================================+
| IDE feedback latency                  | bounded by next Sphinx rebuild        | direct file access via TOML           |
+---------------------------------------+---------------------------------------+---------------------------------------+
| As-you-type validation                | not feasible (Sphinx is a batch tool) | works on real files directly          |
+---------------------------------------+---------------------------------------+---------------------------------------+
| Live preview                          | autobuild-based                       | ``sphinx-autobuild`` works as-is      |
+---------------------------------------+---------------------------------------+---------------------------------------+
| "Go to definition" lands in           | the materialized copy under bazel-bin | the real source file                  |
+---------------------------------------+---------------------------------------+---------------------------------------+
| ``conf.py`` execution required for IDE| yes                                   | no — TOML is enough                   |
+---------------------------------------+---------------------------------------+---------------------------------------+
| Sandbox-friendly Bazel build          | yes                                   | yes                                   |
+---------------------------------------+---------------------------------------+---------------------------------------+

The two approaches are not mutually exclusive — a materialized-tree
rule can coexist if a downstream consumer needs it. But sphinx-mounts
is the lighter-weight surface and the primary entry point for new
bundles.


Using mounts in ``docs()``
--------------------------

The ``docs()`` macro accepts a ``mounts`` parameter taking a list of
``mount(...)`` entries:

.. code-block:: starlark

   load("//:docs.bzl", "docs", "mount")

   docs(
       data = [
           "@score_process//:needs_json",
       ],
       mounts = [
           mount(
               label = "//src:docs_dir",
               mount_at = "internals/code_docs",
               attach_to = "internals/index",
               src_root = "src/docs",
           ),
       ],
       source_dir = "docs",
   )

Each argument:

* ``label`` — a Bazel label that produces a **single output
  directory** suitable for sphinx-mounts to walk. For in-repo bundles,
  use the ``files_to_dir`` helper from ``docs.bzl`` (see
  below). External labels work the same way — for example
  ``"@some_upstream//:docs_dir"``.

* ``mount_at`` — the docname prefix at which the bundle appears in
  the host project. With ``mount_at = "internals/code_docs"``, a
  bundle file ``overview.rst`` is reachable in the host as the
  docname ``internals/code_docs/overview``.

* ``attach_to`` (optional) — a host docname whose toctree should
  automatically receive the bundle's entry document. With
  ``attach_to = "internals/index"``, the bundle's ``index`` doc is
  appended to the first toctree in ``docs/internals/index.rst`` at
  build time; that host doc does not need a manual entry.

* ``entry_doc`` (optional, default ``"index"``) — the
  mount-relative docname of the bundle's entry document, used in
  conjunction with ``attach_to``.

* ``src_root`` (optional) — the in-repo path of the bundle's source
  directory (for example ``"src/docs"``). When set, a per-bundle
  ``ubproject.toml`` is generated at that path during
  ``bazel run //:docs_check`` so that ubCode resolves the
  project's type system when opening files inside the bundle. The
  generated file is gitignored. See `Per-bundle ubproject.toml`_.


Exposing a directory artifact with ``files_to_dir``
---------------------------------------------------

sphinx-mounts walks one directory per mount, so the macro needs a
Bazel target that produces a single output directory rather than a
filegroup. The ``docs.bzl`` macro file exports a small Starlark rule,
``files_to_dir``, that materializes a glob of files into a single
``ctx.actions.declare_directory(...)`` output under ``bazel-bin``.

A typical in-repo usage:

.. code-block:: starlark

   # src/BUILD
   load("//:docs.bzl", "files_to_dir")

   files_to_dir(
       name = "docs_dir",
       srcs = glob(["docs/**/*.rst"]),
       strip_prefix = "src/docs/",
       visibility = ["//visibility:public"],
   )

The resulting target ``//src:docs_dir`` is the right shape to pass to
``mount(label = ...)``. The ``strip_prefix`` attribute trims the
package-relative prefix off each source path so the bundle is laid out
the way the mount expects.


How the wiring works
--------------------

The pieces fit together like this:

.. code-block:: text

   docs(mounts = [...])         ← BUILD declares mounts
            │
            ▼
   docs.bzl                     ← sets env MOUNTS = '[{...}]'
                                  bundles mount runfiles
            │
            ▼
   sphinx-build
            │
            ▼
   score_mounts extension       ← parses MOUNTS, computes two paths:
                                   • absolute runfile path (for sphinx-mounts)
                                   • portable bazel-bin path (for the TOML)
            │
        ┌───┴────┐
        ▼        ▼
   sphinx_mounts   needs_config_writer
   walks the dir    writes docs/ubproject.toml with the
   via abs path     portable [[mounts]] block

After a successful ``bazel run //:docs_check``, the host's
``docs/ubproject.toml`` contains a ``[[mounts]]`` entry like:

.. code-block:: toml

   [[mounts]]
   dir = "../src/docs"
   mount_at = "internals/code_docs"
   attach_to = "internals/index"

The ``dir`` value points at the bundle's **real source location**
(here, ``src/docs/`` — the directory passed to the mount via
``src_root``), not at the materialised bazel-bin copy. ubCode and
similar tools that follow this mount entry therefore navigate to
the original files; jump-to-definition and ``git blame`` work as
the author wrote them.

This block is what every external consumer of the project (ubCode,
sphinx-build, CI) reads to discover the bundle.

The architectural symmetry with the existing
``data = [@x//:needs_json]`` flow is intentional — mounts
travel the same transport (a JSON env var), the same runfiles
resolver, and the same TOML serializer (``needs-config-writer`` via
``score_sync_toml``).

Building from Bazel
~~~~~~~~~~~~~~~~~~~

Three relevant targets are wired by the ``docs()`` macro:

* ``bazel run //:docs`` — incremental HTML build for day-to-day
  editing; outputs to ``_build/``. Resolves mounts via runfiles
  (fast, dev-local).

* ``bazel run //:docs_check`` — same as above but with the ``check``
  action; also regenerates ``docs/ubproject.toml`` (host) and any
  bundle ``ubproject.toml`` (e.g. ``src/docs/ubproject.toml`` for
  the demo mount). Run this after editing the mount list or to
  refresh the IDE-facing TOML.

* ``bazel build //:docs_html`` — sandboxed HTML build. Outputs to
  ``bazel-bin/docs_html/_build/html/``. Useful in CI; verifies that
  mounted bundles resolve correctly without ``bazel run``.

``bazel build //:needs_json`` (also sandboxed) keeps working with
mounts active — the existing needs-only path is unchanged.


Per-bundle ``ubproject.toml``
-----------------------------

When a ``mount(...)`` entry sets ``src_root``, the ``docs()`` macro
arranges for a bundle ``ubproject.toml`` to be generated at that
path during ``bazel run //:docs_check``.

The generated file is a **sanitized copy** of the host's TOML. It
preserves:

* ``[[needs.types]]`` — the project's need types (req, spec,
  feat_req, ...).
* ``[needs.links]`` — link kinds (satisfies, fulfils, ...).
* ``[needs.layouts]`` — display layouts.
* ``[needs.fields.*]`` — field defaults.
* ``[needs.flow_configs]`` / ``[needs.graphviz_styles.*]`` — diagram
  configuration.
* ``[parse.extend_directives.*]`` — parsing extensions.
* ``[server]`` — ubCode server settings.

And drops:

* Top-level ``mounts = [...]`` — bundles never nest mounts.
* ``needs.external_needs`` — relative paths that would not resolve
  from the bundle's location.
* ``needs.schema_definitions_from_json``,
  ``needs.schema_debug_path``, ``needs.build_needumls`` — host-only
  filesystem paths.

The bundle TOML is gitignored. Each bundle's ``.gitignore`` entry
should be added explicitly per ``src_root`` to avoid masking real
configuration files elsewhere.


Caveats and known limitations
-----------------------------

* **Workspace-only generation.** The bundle ``ubproject.toml`` is
  written only under ``bazel run`` (when
  ``BUILD_WORKSPACE_DIRECTORY`` is available). Sandboxed builds skip
  it; this is by design — the sandbox's workspace mirror is discarded
  after the build.

* **External-repository bundles.** The current implementation focuses
  on in-repo bundles. Mounting a bundle from another Bazel module
  works for the host build, but ``src_root`` does not apply because
  the bundle's source files do not live in this repository's workspace.

* **No mount nesting.** Bundles do not themselves declare mounts.
  A bundle's ``ubproject.toml`` always has the top-level ``mounts``
  array stripped.

* **One `files_to_dir` per bundle.** Each mount must point at a
  single output directory. The ``files_to_dir`` helper is the
  recommended way to assemble a directory from a ``glob``; other
  shapes (e.g. a ``sphinx_docs_library``) are not yet supported.


Cross-bundle references work
----------------------------

A need authored inside a mounted bundle can be linked from anywhere in
the host project, just like a need authored in ``docs/`` itself. For
example, the stakeholder requirement that motivates this feature lives
in the mounted "Code Docs" bundle at ``src/docs/requirements.rst``,
and the host-side ``tool_req__docs_mount_traceability`` carries a
``:satisfies:`` link directly to it:

   See :need:`stkh_req__docs__mounts` — a stakeholder requirement
   authored in the mounted bundle, satisfied by a tool requirement
   in ``docs/``, with the link enforced by ``sphinx-needs`` schema
   validation.

That cross-boundary link uses only stock relations from
``score_metamodel`` (``tool_req`` may satisfy ``stkh_req`` without any
metamodel extension): the bundle owns its own ``.rst`` and lives next
to its code, but its needs participate in the host's traceability
graph as first-class citizens.


Further reading
---------------

* `sphinx-mounts documentation`_ — full configuration reference,
  TOML schema, behaviour of ``attach_to`` and ``entry_doc``.
* `ubCode`_ — the IDE extension that reads ``ubproject.toml``.
* :doc:`add_extensions` — how to plug other Sphinx extensions into
  the docs-as-code build.

.. _sphinx-mounts documentation: https://sphinx-mounts.useblocks.com/
.. _ubCode: https://ubcode.useblocks.com/

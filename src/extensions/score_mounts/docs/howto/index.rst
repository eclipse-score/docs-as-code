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

Mounting external source bundles
================================

This guide explains how to surface RST or Markdown content that lives
**outside** ``docs/`` into the docs-as-code build.

.. contents::
   :local:
   :depth: 2

Declaring a bundle with ``docs_bundle``
---------------------------------------

A mountable bundle carries only **content**: the source files. It is a
Bazel target created with the ``docs_bundle`` rule from ``docs.bzl``,
declared next to the bundle's sources:

.. code-block:: starlark

   # src/BUILD
   load("//:docs.bzl", "docs_bundle")

   docs_bundle(
       name = "docs_dir",
       source_dir = "docs",
       visibility = ["//visibility:public"],
   )

Each attribute:

* ``source_dir`` — directory holding the bundle's own doc sources. It is
  globbed the same way as ``docs()`` (RST, Markdown, images, and the
  other doc file kinds). The ``source_dir`` itself *is* the mount root, so
  the files mount relative to it (``docs/index.rst`` becomes ``index.rst``).
  The bundle exposes those files as a Bazel depset (via the
  ``DocsBundleInfo`` provider) and records the ``source_dir`` path;
  sphinx-mounts walks that original directory directly — no copy is made.

The bundle carries **no placement** — where it appears in a host project
is decided by the *consumer*, so the same bundle can be mounted at
different locations by different consumers (see the next section).

Placement at the consumer: ``docs(bundles=[...])``
---------------------------------------------------

The ``docs()`` macro's ``bundles`` argument is a list of placement dicts.
Each dict pairs a bundle label with where it goes in *this* project:

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

Each placement key:

* ``bundle`` — label of a ``docs_bundle`` target (in-repo or from another
  module, see :ref:`cross-repo mounts <cross_repo_mounts>`).

* ``mount_at`` — the docname prefix at which the bundle appears in the
  host project. With ``mount_at = "internals/code_docs"``, a bundle file
  ``overview.rst`` is reachable in the host as the docname
  ``internals/code_docs/overview``.

* ``attach_to`` (optional) — a host docname whose toctree should
  automatically receive the bundle's entry document. With
  ``attach_to = "internals/index"``, the bundle's ``index`` doc is
  appended to the first toctree in ``docs/internals/index.rst`` at build
  time; that host doc does not need a manual entry.

* ``entry_doc`` (optional, default ``"index"``) — the mount-relative
  docname of the bundle's entry document, used together with
  ``attach_to``.

The bundle's ``dir`` in the generated ``ubproject.toml`` is **derived
automatically** from the source file paths — there is no ``src_root``
attribute.

Every project that uses ``docs()`` also **auto-exposes its own**
``source_dir`` as a public bundle named ``docs_bundle``. No extra
wiring is needed: because a consumer's ``docs()`` call *is* this macro,
``@<module>//:docs_bundle`` exists for free and can be mounted elsewhere.

Composing bundles
-----------------

A ``docs_bundle`` may itself mount other bundles through its ``bundles``
argument, so one bundle can aggregate a whole sub-tree of content. Each entry
uses the same placement keys as ``docs(bundles=[...])`` (``bundle``, ``mount_at``,
optional ``attach_to`` / ``entry_doc``), but the placement is *relative to the
composing bundle* rather than to a host project:

.. code-block:: starlark

   docs_bundle(
       name = "guide",
       source_dir = "guide",
       bundles = [
           {"bundle": "//some/pkg:api_docs", "mount_at": "reference", "attach_to": "index"},
       ],
   )

Here ``guide`` bundles ``api_docs`` under ``reference`` and attaches its entry
doc to ``guide``'s own ``index``. ``guide`` is still **placement-free**: when a
consumer mounts ``guide`` at, say, ``mount_at = "internals/code_docs"``, the two
placements **prefix-stack**. The nested ``api_docs`` then resolves to
``internals/code_docs/reference`` in the host, and its ``attach_to`` resolves to
``internals/code_docs/index``. Composition is therefore fully transitive: a
bundle nested any number of levels deep lands at the concatenation of every
``mount_at`` above it.

If the **same** underlying bundle resolves to two different final ``mount_at``
values (for example, mounted both directly and again via a composing bundle), the
build fails hard with a ``mount conflict … a bundle must resolve to a single
mount_at`` error — duplicating a bundle's pages would collide docnames and need
IDs. See :ref:`docs_concept_mounts` for the composition semantics.

.. _cross_repo_mounts:

Cross-repo mounts
-----------------

A bundle label in ``bundles`` may point at another Bazel module's
auto-exposed bundle. For example, this repository mounts the process
description — already a dependency and itself a ``docs()`` user — with:

.. code-block:: starlark

   bundles = [
       {"bundle": "@score_process//:docs_bundle", "mount_at": "process", "attach_to": "index"},
   ]

Mounting an external bundle also mounts the Need directives authored in that
module's sources. Do not add the same module's ``:needs_json`` to ``data``:
that would import a second copy of every Need and Sphinx-Needs rejects the
duplicate IDs. Use ``data = ["@module//:needs_json"]`` only for a JSON-only
dependency whose documentation sources are not mounted. If that module mounts
further external modules for its own site, those are not re-exported; mount each
such module explicitly when it is wanted in this project.

For an **external** bundle the sources do not exist in the consumer's
git tree; they live under ``bazel-*/external/<module>+/…``. The ``dir``
in ``ubproject.toml`` therefore points at the staged source directory under
``bazel-bin/external/<module>+/…`` — the same pattern already used for
external ``needs.json`` (``json_path = "bazel-bin/external/…"``).
"Go to definition" for such a mount lands in that read-only staged module
tree, not in an editable source file. In-repo bundles keep pointing at their
real, editable sources.


How the wiring works
--------------------

The pieces fit together like this:

.. code-block:: text

   docs_bundle(...) in a BUILD    ← bundle: files depset + mount root
            │                        (DocsBundleInfo provider, content only)
            ▼
   docs(bundles = [{"bundle": "//src:docs_dir", "mount_at": ...}])
            │                        placement lives at the call site
            ▼
   docs.bzl: _mounts_manifest rule ← reads the providers + placement,
                                    derives each bundle's source dir from
                                    the file paths, and emits ONE canonical
                                    JSON manifest
            │
            ▼
   sphinx-build (mounts_manifest = manifest path)
            │
            ▼
   score_mounts extension         ← reads the manifest and configures runtime
                                    mounts plus neutral metadata:
            │
        ┌───┴────┐
        ▼        ▼
   sphinx_mounts   score_sync_toml
   walks the dir    derives TOML paths, serializes and merges /ubproject.toml

The key inversion from earlier iterations: **Bazel is the single
source of truth for mount paths**. All paths are computed in the rule,
where ``File`` objects have real paths, instead of being reconstructed
from label strings at Sphinx runtime.

After a successful ``bazel run //:docs_check``, the repo-root
``ubproject.toml`` contains a mount entry like:

.. code-block:: toml

   mounts = [
       { dir = "src/docs", mount_at = "internals/code_docs", attach_to = "internals/index" },
   ]

The ``dir`` value points at the bundle's **real source location**
(here, ``src/docs/`` — derived automatically from the bundle's source
files), not at any bazel-bin path. It is relative to the
``ubproject.toml`` location (the git root). ubCode and similar tools
that follow this mount entry therefore navigate to the original files;
jump-to-definition and ``git blame`` work as the author wrote them.

This block is what every external consumer of the project (ubCode,
sphinx-build, CI) reads to discover the bundle.

``score_sync_toml`` serializes the structured entries to TOML and passes that
temporary fragment to ``needs-config-writer``, the same writer that emits the
rest of the project's type system. Bazel never emits TOML.

Building from Bazel
~~~~~~~~~~~~~~~~~~~

Relevant targets wired by the ``docs()`` macro:

* ``bazel run //:docs`` — incremental HTML build for day-to-day
  editing; outputs to ``_build/``. Resolves mounts via runfiles
  (fast, dev-local).

* ``bazel run //:docs_check`` — same as above but with the ``check``
  action; also regenerates the repo-root ``ubproject.toml``. Run this
  after editing the mount list or to refresh the IDE-facing TOML.

* ``bazel build //:needs_json`` — sandboxed needs-only build. Verifies
  that mounted bundles resolve correctly without ``bazel run``.


A single ``ubproject.toml`` at the git root
--------------------------------------------

The whole project — host and every mounted bundle — is described by
**one** ``ubproject.toml`` at the git repo root. ``needs-config-writer``
relativizes every path field against the output file's directory, so
anchoring the file at the root makes ``external_needs`` JSON paths, the
mount ``dir`` values, and schema paths all root-relative and valid for
any consumer that reads them from there.

The output location is set by ``score_sync_toml`` to
``find_git_root() / "ubproject.toml"``. ``find_git_root()`` resolves the
repo root both under ``bazel run`` and under esbonio / direct Sphinx
(via a working-directory fallback), so the file lands at the root in
every IDE-facing context. In a sandboxed ``bazel build`` there is no
git root; the writer falls back to the confdir default and that copy is
discarded with the sandbox.

The file is gitignored (``/ubproject.toml``): it is regenerated on
every build and is not a source artifact.


Caveats and known limitations
-----------------------------

* **External-repository bundles read the staged bazel-bin tree.** Bundles
  from another Bazel module are supported (see :ref:`cross_repo_mounts`), but
  their ``dir`` points at the staged ``bazel-bin/external/…`` source tree
  rather than at editable sources, and that tree only exists after a
  build.

* **One source directory per bundle.** A bundle's content is a single
  ``source_dir``; that directory is exactly the mount-relative tree
  sphinx-mounts walks, so there is no cross-directory layout to reconcile.

* **Standard confdir assumption.** Anchoring at the git root assumes
  the git root is an ancestor of every source tree (host and bundles),
  which holds for the standard layout. A repo whose sources live
  outside its git tree would need a different anchor.


Cross-bundle references work
----------------------------

A need authored inside a mounted bundle can be linked from anywhere in
the host project, just like a need authored in ``docs/`` itself. This
page *is* a mounted bundle, so we dogfood it directly: the stakeholder
requirement below is authored right here, in the mounted score_mounts
how-to bundle, yet the host-side ``tool_req__docs_mount_traceability``
(in ``docs/internals/requirements/``) carries a ``:satisfies:`` link
straight to it.

The link resolves at host build time with no copy or materialisation,
and is enforced by ``sphinx-needs`` schema validation. That
cross-boundary link uses only stock relations from
``score_metamodel`` (``tool_req`` may satisfy ``stkh_req`` without any
metamodel extension): the bundle owns its own ``.rst`` and lives next
to its code, but its needs participate in the host's traceability
graph as first-class citizens.


Further reading
---------------

* `sphinx-mounts documentation`_ — full configuration reference,
  TOML schema, behaviour of ``attach_to`` and ``entry_doc``.
* `ubCode`_ — the IDE extension that reads ``ubproject.toml``.
* :ref:`howto_add_extensions` — how to plug other Sphinx extensions into
  the docs-as-code build.

.. _sphinx-mounts documentation: https://sphinx-mounts.useblocks.com/
.. _ubCode: https://ubcode.useblocks.com/

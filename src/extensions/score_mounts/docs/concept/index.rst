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

.. _docs_concept_mounts:

======================================
Mounts: which directory Sphinx walks
======================================

Mounting another documentation bundle into this project's Sphinx tree grafts the
*contents of one directory* into the doc tree. This page explains which directory
that is — and why it is always the bundle's **original files**, never a copy.

For the user-facing "how do I mount another module" guide, see
:ref:`howto_mount_external_sources`.

Mounting overlays a directory
=============================

**Mounting** is the placement/overlay operation: at runtime ``sphinx_mounts``
takes the contents of one directory and grafts them into the doc tree at the
bundle's ``mount_at`` (optionally attached under ``attach_to``). A ``docs_bundle``
with a ``source_dir`` contributes exactly that directory.

A ``source_dir`` bundle **is already a mount-ready directory**: its files sit on
disk under ``source_dir`` in the layout they should mount in. So the bundle makes
no copy — it only records the *mount root* (the ``source_dir`` path as a Bazel
``short_path``) and lets ``sphinx_mounts`` walk the real files. Sphinx therefore
always operates on the originals, which keeps live preview and jump-to-definition
pointing at editable source.

Transitive composition
=======================

A ``docs_bundle`` exposes its content through the ``DocsBundleInfo`` provider,
whose ``entries`` field is an **ordered list** of placed content entries.
When a bundle composes children (via ``bundles = [...]``), each child's entries
are appended in declaration order and re-based under the child's ``mount_at``.
A mounter therefore sees one flat, ordered list regardless of how deeply the
graph nests.

**Placement composes by prefix-stacking.** A bundle is placement-free; its own
root takes the placement it is mounted with, and every nested entry gets the
enclosing ``mount_at`` (and ``attach_to``) prefixed onto its own. A child mounted
at ``mount_at = "child"`` inside a parent that is later mounted at
``internals/code_docs`` resolves to ``internals/code_docs/child``. Resolution is
independent of nesting depth.

**One bundle, one placement.** After the graph is flattened, the same underlying
bundle directory resolving to two different final ``mount_at`` values is a hard
build error (``mount conflict … a bundle must resolve to a single mount_at``).
The same directory at the *same* ``mount_at`` is simply deduplicated.

**Composition stops at external module boundaries.** A module may mount another
module for its own documentation build. When a third module mounts the first,
it receives the first module's source tree and in-repo bundles, but not foreign
modules the first one mounted. Consumers opt in to every external module
explicitly, keeping ownership and collision handling predictable.

For data-only integration, **needs stay one ``needs.json`` per module**. A
consumer that imports another module's ``needs.json`` does not mount its sources;
cross-module references then use the external-needs mechanism. A consumer that
mounts a bundle instead builds the mounted sources and Need directives as part
of its own Sphinx project.

Which directory gets walked
===========================

The runtime resolver (``score_mounts``) picks the directory per mount — always an
original source directory, differing only in *where* that directory is staged:

.. code-block:: python

   if spec.external and ws_root:  # bazel run: sibling repo in the runfiles tree
       walk_dir = manifest.runtime_dir(spec)
   elif ws_root is not None:      # bazel run, in-tree: the live workspace source
       walk_dir = ws_root / spec.src_root
   else:                          # sandbox, in-tree: source staged at the exec root
       walk_dir = Path(os.path.abspath(spec.src_root))

* ``ws_root`` is only set under ``bazel run`` (it points at
  ``BUILD_WORKSPACE_DIRECTORY``); in a sandboxed ``bazel build`` it is ``None``.
* ``external`` marks a bundle whose sources come from another Bazel module.
* The manifest (a ``bazel-out`` artifact) is colocated with the sources only in the
  runfiles tree; in a sandbox the in-tree sources are resolved against the exec
  root instead, which is why the branch splits three ways.

So the mount walks:

* the **live workspace source** under ``bazel run`` with an in-tree bundle (edits
  show up immediately — best for live preview and jump-to-definition);
* the **in-place staged inputs** in a sandbox build (``needs_json``), where only
  the bundle's globbed files are present at their ``source_dir`` path;
* the **staged sibling-repo directory** for an external bundle under
  ``bazel run`` (``../<repo>+/source_dir`` in the runfiles tree), or its
  ``external/<repo>+/source_dir`` execroot path in a sandboxed build.

In all three cases the payload is the untouched source directory; a stray file
that is not doc source (e.g. a ``conf.py``) is simply ignored by Sphinx.

Without an external bundle declaration, a dependency is referenced via its
prebuilt ``needs.json`` and its sources are not walked at all.

.. _docs_concept_mounts_rematerialize:

Re-introducing materialization later
====================================

Earlier versions copied each bundle into a normalized ``declare_directory`` at
build time ("materialization"). That was dropped because a ``source_dir`` bundle
is *already* a mount-ready directory — the copy was a byte-for-byte duplicate of a
directory Bazel stages anyway. This section records how to bring materialization
back should the bundle model grow beyond whole-``source_dir`` inputs.

.. note::

   Materialization should be a **last resort**. Before re-adding a build-time
   copy, investigate whether ``sphinx_mounts`` can already express the need
   directly — e.g. a **file/glob mode** or **include/exclude filtering** on the
   mount itself. Filtering a subset or picking individual files at the mount layer
   avoids duplicating the tree and keeps Sphinx pointed at the originals; prefer
   that over reintroducing a copy action.

**When it becomes necessary.** Materialization earns its keep only when a bundle
is *not* already one ready-to-mount directory on disk *and* ``sphinx_mounts``
cannot select the payload itself:

* **File globs / a filtered subset** — the bundle is an explicit list of files
  rather than a whole directory, so no single existing directory holds exactly the
  payload.
* **A custom ``strip_prefix``** that differs from the files' on-disk layout — the
  mount-relative paths then exist only in a rewritten tree.
* **Provider-supplying rules** — a rule that emits ``DocsBundleInfo`` for content
  it *generates* (no stable on-disk source directory to point at).

**Sketch of the mechanism** (intentionally high level — flesh out when needed):

#. In the bundle rule, ``ctx.actions.declare_directory(name)`` and a copy action
   assemble the normalized, mount-relative tree from ``ctx.files.srcs``.
#. The content entry then carries that directory ``File`` (alongside, or instead
   of, ``runtime_path``); the emitted ``runtime_path`` points at it.
#. A materialized directory is a ``bazel-out`` artifact colocated with the manifest
   in every context, so it resolves via ``manifest.runtime_dir`` — the same
   manifest-relative rule the external branch already uses. That sidesteps the
   exec-root vs. runfiles split the in-tree source walk has to handle, which is
   the resolver-simplicity that materialization used to buy.

**Provider contract.** A content entry must let the runtime resolve a directory to
walk. Today that is ``runtime_path`` (a source-directory ``short_path``) plus
``src_root`` (the live in-tree path, empty for external). A materialized entry
would instead (or additionally) carry a directory ``File`` whose ``short_path``
serves as ``runtime_path``. Either representation is valid as long as
the mount-entry deduplication has a stable identity key and ``_mounts_manifest`` can emit a
``runtime_path``.


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
project uses. A file inside ``docs/`` and a file inside a **mounted**
bundle (for example, ``src/docs/overview.rst``) live in different
subtrees, so no single ``ubproject.toml`` placed *inside* either tree
is visible from the other.

To close this gap, the toolchain emits a **single** ``ubproject.toml``
at the **git repo root** — the one directory that is an ancestor of
both ``docs/`` and every in-repo bundle. The walk-up from any source
file therefore reaches it. Because it is the only config file, it
carries the host's full type system *and* the ``[[mounts]]`` entries;
there are no sanitized per-bundle copies to keep in sync.


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

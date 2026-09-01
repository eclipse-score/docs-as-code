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

.. _score_mounts_internals:

Mounts extension internals
==========================

This page is for maintainers of ``score_mounts``. User-facing bundle and mount
semantics are documented in :ref:`docs_concept_mounts`; BUILD usage is in
:ref:`howto_mount_external_sources`.

Architecture and manifest contract
----------------------------------

``docs.bzl`` owns bundle graph traversal. Its ``_mounts_manifest`` rule turns
the ``DocsBundleInfo`` provider graph and each consumer placement into one JSON
manifest. Python deliberately receives paths rather than Bazel labels, so it
does not reconstruct Bazel repository names at Sphinx runtime.

Each manifest entry contains:

* ``src_root`` — the source directory relative to the main workspace or the
  sandbox execroot;
* ``runtime_path`` — the Bazel short path used when a staged directory must be
  walked;
* ``mount_at`` and ``attach_to`` — the already-composed Sphinx placement; and
* ``entry_doc`` — the canonical entry document declared by the source bundle.
* ``external`` — whether the directory belongs to another Bazel module.

At ``config-inited``, ``score_mounts`` resolves all directory source mounts before
constructing ``config.mounts``. A mount below Sphinx's primary source directory
is added to the primary ``exclude_patterns`` as a relative ``<mount>/**`` pattern.
A mount below another mount is added to the parent entry's ``sphinx-mounts``
``exclude`` patterns. This prevents a document from being discovered by both its
containing directory walk and its owning mount. Because the exclusions are
directory patterns rather than a snapshot of source files, newly created files
remain visible to live preview.

Explicit ``docs_bundle(srcs = [...])`` entries remain in file-list mode and are
not included in these directory exclusions. They are intended for generated
sources outside the primary source tree; an explicitly mounted workspace file
below a walked root is a known limitation and would need exact-file exclusions.

The rule rejects conflicting final placements before Sphinx starts. A mount
without ``attach_to`` is attached to the ``index`` document beside its
``mount_at``; ``attach_to`` overrides that target. The Python
extension may therefore preserve declaration order and only translates each
manifest entry into the ``sphinx_mounts`` configuration format.

Directory resolution
--------------------

``score_mounts._resolver.resolve_walk_dir`` selects the directory that
``sphinx_mounts`` walks. The source directory is never copied.

+------------------------------+-----------------------------------------------+
| Build context                | Directory used                                |
+==============================+===============================================+
| ``bazel run``, in-tree       | live ``BUILD_WORKSPACE_DIRECTORY / src_root`` |
+------------------------------+-----------------------------------------------+
| sandboxed build              | staged ``execroot / src_root``                |
+------------------------------+-----------------------------------------------+
| ``bazel run``, external      | sibling repository in the runfiles tree       |
+------------------------------+-----------------------------------------------+

External short paths begin with ``../<repo>+`` relative to the runfiles
``_main`` directory. The resolver therefore prefixes ``_main`` before turning
that path into an absolute path. This distinction is covered by unit tests and
the public ``docs_bzl`` integration suite; do not resolve an external runtime path
relative to the manifest file, because the manifest can live below a Bazel
package directory.

Incremental builds use the same resolver in ``src/incremental.py`` to add every
mounted directory to ``sphinx-autobuild``'s watch list. Keep these two call
sites aligned when the manifest contract changes.

TOML synchronization
--------------------

``score_mounts`` writes structured mount entries to ``config.mounts`` during
``config-inited``. ``score_sync_toml`` then serializes them through
``needs-config-writer`` into the repository-root ``ubproject.toml``. The
generated file is intentionally shared by the host and all in-tree bundles so
IDE tooling can discover one configuration while walking up from either source
tree.

The ordering is significant: ``score_mounts`` runs before ``sphinx_mounts`` so
the manifest is authoritative at build time, and ``score_sync_toml`` runs after
it so the TOML writer sees the resolved structured entries.

Why bundles are not materialized
--------------------------------

A ``source_dir`` bundle already has the mount-relative layout on disk.
Materializing a second directory would duplicate its files, point navigation at
a generated copy, and add a build action without changing the Sphinx input.

Reconsider materialization only if a future bundle cannot be represented by one
existing directory, for example for a filtered file set, a custom
``strip_prefix``, or generated provider content. Prefer native filtering support
in ``sphinx_mounts`` first. If a copy action becomes necessary, extend the
manifest with a directory artifact and keep its identity stable for placement
deduplication.

Validation
----------

Relevant checks are:

* ``bazel test //src/extensions/score_mounts:score_mounts_tests`` for manifest
  parsing and path resolution;
* ``.venv_docs/bin/python -m pytest -vv src/tests/docs_bzl/test_nested_bundles.py
  src/tests/docs_bzl/test_external_bundle.py
  src/tests/docs_bzl/test_invalid_bundle_placements.py`` for
  mounted rendering, toctree attachment, external bundles under ``bazel run``,
  sandboxed external builds, and placement conflicts; and
* ``bazel test //...`` for the internal extension unit tests.

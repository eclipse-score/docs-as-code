..
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   SPDX-License-Identifier: Apache-2.0

Overview
========

The ``src/`` directory contains the Python extensions and Bazel helpers
that make up the docs-as-code toolchain. This "Code Docs" bundle
documents that surface — kept next to the code so it can evolve with
the code, and mounted into the host docs site via ``sphinx-mounts``.

Files live under ``src/docs/`` in the repository but are visible to
the host at the docname prefix ``_mounted/internal/``.

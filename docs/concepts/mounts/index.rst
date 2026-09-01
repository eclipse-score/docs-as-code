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

Documentation bundles and mounts
================================

Documentation does not always live in a project's ``docs/`` directory. A
library may keep its reference material next to its source code, and a Bazel
module may want to contribute its own documentation to another module's site.
Bundles and mounts make that content part of one Sphinx project without copying
it.

For the commands and BUILD declarations, see
:ref:`howto_mount_external_sources`.

Bundle, mount, and placement
----------------------------

A **bundle** is a named, mountable documentation directory. It owns its
content, but not its position in a consuming documentation site.

A **mount** makes a bundle visible in a host site. The host chooses the
**placement** with ``mount_at``. The bundle defines its own ``entry_doc``
(default ``index``); the mount adds that page to the parent ``index`` toctree
by default. ``attach_to`` overrides that host toctree document. This separation
lets different projects reuse the same bundle at different locations while
preserving its canonical entry page.

Bundles are read from their original source directories. Consequently, an
in-repository bundle remains editable and IDE navigation reaches its real
source files rather than generated copies.

Composition
-----------

A bundle can contain placements for other bundles. Placements compose by
prefixing their paths: a child placed at ``reference`` inside a guide that is
mounted at ``internals/code_docs`` appears at
``internals/code_docs/reference``.

A bundle must have one final location in a documentation build. If the same
bundle would resolve to two different locations, the build fails instead of
creating colliding docnames or Need IDs. Repeating the same placement is
deduplicated.

Source directories are also ownership boundaries. When a mounted bundle lives
physically below the host's source directory, the host Sphinx walk excludes the
bundle subtree and the bundle mount discovers it. When a bundle contains a
child bundle below its own source directory, the parent mount excludes the
child subtree and the child mount discovers it. These are directory exclusions,
so new files remain discoverable during live preview without being discovered
twice.

External modules and Needs
--------------------------

A bundle from another Bazel module is mounted like an in-repository bundle, but
its files are read from Bazel's staged dependency tree. They are useful for
published documentation but are not editable from the consuming checkout.

Mounted sources participate in the host's Sphinx-Needs project, including their
Need directives and cross-bundle references. By contrast, importing a module's
``needs.json`` is a data-only integration: its sources are not mounted. Do not
use both mechanisms for the same module in one build, because that would import
the same Need IDs twice.

Mounting an external module does not implicitly mount the external modules it
uses itself. Consumers select each external documentation dependency explicitly;
this keeps the published structure and ownership clear.

Editor support and generated configuration
------------------------------------------

The build writes one ``ubproject.toml`` at the repository root. It describes
the host and its mounted directories for Sphinx, ubCode, and similar tools.
Because the file is an ancestor of both ``docs/`` and in-repository bundle
directories, editor tooling can discover one consistent project configuration
from either location.

Run ``bazel run //:docs`` or ``bazel run //:docs_check`` after changing mounts
to refresh this generated, gitignored file. A sandboxed ``needs_json`` build
checks the same mount configuration without producing a persistent local file.

Design rationale
----------------

The bundle model deliberately keeps content ownership separate from site
placement and avoids materializing copies merely to arrange documentation.
That follows the infrastructure direction in
`DR-008-infra <https://eclipse-score.github.io/score/main/design_decisions/DR-008-infra.html>`_.
It keeps source navigation useful while allowing Bazel modules to compose their
documentation in a reproducible build.

Further reading
---------------

* :ref:`howto_mount_external_sources` — declare and mount bundles.
* `sphinx-mounts documentation <https://sphinx-mounts.useblocks.com/>`_ —
  configuration reference, including ``attach_to`` and ``entry_doc``.

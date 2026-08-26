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

.. _howto_generated_docs:

Integrate Generated Documentation
=================================

When a script or tool creates documentation content at build time, collect it
with a ``docs_bundle`` and mount the bundle into your documentation tree.

You find a `complete working example <https://github.com/eclipse-score/docs-as-code/tree/main/src/extensions/score_metamodel/docs/>`_
in the :ref:`metamodel-types-visualization`.

Which ``data`` attribute?
-------------------------

For a mounted documentation bundle, put the generated files in
``docs_bundle(data = [...])``. Those files are part of the bundle payload: they
travel with the bundle and are resolved below its eventual ``mount_at`` path.

``docs(data = [...])`` is different. It adds files to the project-level
``docs()`` build, outside any bundle, and therefore gives those files no bundle
mount path. Use it only for inputs that belong to the project-level build. If
the file is documentation, an image, or a supporting asset for a bundle, put
it in that bundle instead.

For this how-to, the rule is simple: generated documentation belongs in
``docs_bundle(data = [...])``.

Step 1: Generate the RST Files
------------------------------

Use a ``genrule`` (or **any build action**) that writes RST files.

.. code-block:: starlark
   :caption: In your BUILD file

   genrule(
       name = "generate_design_rst",
       srcs = ["design_model.yaml"],
       outs = ["generated/index.rst"],
       cmd = "$(location :design_rst_tool) --output $(location generated/index.rst) $<",
       tools = [":design_rst_tool"],
   )

If your tool writes many files (a second RST, a Mermaid ``.mmd`` diagram, or
any other companion asset), add all of them to ``outs``.
Sphinx directives in the RST (for example ``.. mermaid:: arch.mmd``) use
relative paths because all files stay in the same generated directory.

Make sure the generated files include an ``index.rst`` at the root of the
output directory.

Verify:
  ``bazel build :generate_design_rst`` must succeed.
  Inspect the output at ``bazel-bin/<package>/generated/index.rst``.

Step 2: Declare the Bundle
--------------------------

Wrap the generated files in a ``docs_bundle`` with the ``data`` attribute.
Do not use ``srcs`` — that is for handwritten sources in the source tree.

.. code-block:: starlark
   :caption: In your BUILD file

   docs_bundle(
       name = "design_bundle",
       data = [":generate_design_rst"],
   )

This is a **data-only bundle**: it has no ``source_dir`` because all of its
documentation is generated. It is still a normal mountable bundle. The
generated ``index.rst`` becomes the bundle's entry page and travels with the
bundle when it is mounted. A bundle with both handwritten sources and
generated files can use ``source_dir`` and ``data`` together.

Verify:
  ``bazel build :design_bundle`` must succeed.
  The bundle now holds the generated file but does not yet place it anywhere.

Step 3: Mount the Bundle
------------------------

Add the bundle to your ``docs()`` call.

.. code-block:: starlark
   :caption: In your BUILD file

   docs(
       source_dir = "docs",
       bundles = [{
           "bundle": ":design_bundle",
           "mount_at": "design",
           "attach_to": "index",
       }],
   )

The generated page becomes ``design/index.html`` in the output.
``mount_at`` sets the target path; ``attach_to`` adds the page to that
document's toctree (defaults to the parent ``index`` when omitted).

Verify:
  ``bazel run //:docs`` must succeed.
  Open ``_build/design/index.html`` and confirm the generated content.


Common Issues
-------------

**The bundle is mounted but the generated file does not appear, or Sphinx
warns about files not in any toctree.**
Make sure the genrule's ``outs`` uses a subdirectory (for example
``generated/index.rst``) and not a bare ``index.rst``.
``score_mounts`` mounts the parent directory of the genrule output.
Without a subdirectory, it mounts the genrule output root — which often
contains other build artifacts and causes Sphinx warnings.

**Attach-to target is missing.**
``attach_to`` must point to a document that exists in the consuming project's
documentation tree. When unsure, point it at ``"index"`` (the consuming
project's root ``index.rst``).

.. seealso::

   :ref:`docs_concept_mounts` and the :ref:`howto_mount_external_sources` How-To.

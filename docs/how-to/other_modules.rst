Reference Other Modules
=======================

This document explains how to enable cross-module (bi-directional) linking between documentation modules with Sphinx-Needs in this project.
In short:

1. Make the other module available to Bazel via the `MODULE` (aka `MODULE.bazel`) file.
2. Add the external module's documentation targets to your `docs(data=[...])` target so Sphinx can see the other module's built inventory.
3. Reference remote needs using the normal Sphinx-Needs referencing syntax.

Details and Example
-------------------

1) Include the other module in `MODULE.bazel`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The consumer module must declare the other modules as dependencies in the `MODULE.bazel` file so Bazel can fetch them.
There are multiple ways to do this depending on how you manage third-party/local modules (git, local overrides, etc.).

A minimal example (add or extend the existing `bazel_deps` stanza):

.. code-block:: starlark

	 bazel_dep(name = "score_process", version = "1.3.0")

2) Extend your `docs` rule so Sphinx picks up the other module's inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documentation build in this project is exposed via a Bazel macro/rule that accepts a `data` parameter.
Add the external module's ``:needs_json`` target to that list
to have their needs elements available for cross-referencing.

Example `BUILD` snippet (consumer module):

.. code-block:: starlark

    load("@rules_docs//:docs.bzl", "docs")
    docs(
      data = [
         "@score_process//:needs_json",
      ],
      source_dir = "docs",
    )

More details in :ref:`bidirectional_traceability`.

3) Reference needs across modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the other module's are defined as dependencies as explained above, you can reference their needs IDs in the usual Sphinx-Needs way.
The important part is that the inventory name that Sphinx-Needs looks up matches the module that produced the needs entries.

Example in reStructuredText:

.. code-block:: rst

	See the requirement :need:`gd_req__req_traceability`, for example.

Which results in:

   See the requirement :need:`gd_req__req_traceability`, for example.

See the `Sphinx-Needs documentation <https://sphinx-needs.readthedocs.io/en/latest/>`_
for more details on cross-referencing needs.

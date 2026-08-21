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

Reference Docs in Source Code
=============================

In your C++/Rust/Python source code, you want to reference requirements (needs).
The docs-as-code tool will create backlinks in the documentation in two steps:

1. You add a special comment in your source code that references the need ID.
2. Scan for those comments and provide needs links to your documentation.

For an example result, look at the attribute ``source_code_link``
of :need:`tool_req__docs_common_attr_title`.

Comments in Source Code
-----------------------

Use a comment and start with ``req-Id:`` or ``req-traceability:`` followed by the need ID.

.. code-block:: python

    # req-Id: TOOL_REQ__EXAMPLE_ID
    # req-traceability: TOOL_REQ__EXAMPLE_ID

For other languages (C++, Rust, etc.), use the appropriate comment syntax.

Scanning Source Code for Links
------------------------------

In your ``BUILD`` files, pass the implementation targets to the ``docs`` rule
as ``code_targets``. Their ``srcs``, ``hdrs``, and ``textual_hdrs`` are scanned,
including those of their ``deps`` recursively. This means that a
``cc_executable`` also covers source files from the ``cc_library`` targets it
uses. You may also pass filegroups; their files are scanned directly.

.. code-block:: starlark
   :emphasize-lines: 14
   :linenos:

   cc_library(
      name = "some_library",
      srcs = [
          "bar.cpp",
      ],
   )

   cc_executable(
      name = "some_application",
      srcs = ["main.cpp"],
      deps = [":some_library"],
   )

   docs(
      data = [
             "@score_process_description//:needs_json",
         ],
         source_dir = "docs",
         code_targets = [":some_application"],
   )

The older ``scan_code`` parameter remains available for existing configurations
that explicitly provide files or filegroups, but it is deprecated. Prefer
``code_targets`` for new configurations.

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

In you ``BUILD`` files, you specify which source files to scan
with ``filegroup`` or ``glob`` or whatever Bazel mechanism you prefer.
Then, you use the ``sourcelinks_json`` rule to scan those files.
Finally, pass the scan results to the ``docs`` rule as ``sourcelinks`` attribute.


.. code-block:: starlark
   :emphasize-lines: 1, 12, 26
   :linenos:

   load("//:docs.bzl", "docs", "sourcelinks_json")

   filegroup(
      name = "some_sources",
      srcs = [
          "foo.py",
          "bar.cpp",
          "data.yaml",
      ] + glob(["subdir/**/.py"]),
   )

   sourcelinks_json(
      name = "my_source_links",
      srcs = [
         ":some_sources",
         "//src:all_sources",
         # whatever
      ],
   )

   docs(
      data = [
             "@score_process//:needs_json",
         ],
         source_dir = "docs",
         sourcelinks = [":my_source_links"],
   )

Since the source links are Bazel targets, you can easily reference other modules as well.

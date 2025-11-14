Reference Docs in Source Code
=============================

In your C++/Rust/Python source code, you want to reference requirements (needs).
The docs-as-code tool will create backlinks in the documentation.

Use a comment and start with ``req-Id:`` or ``req-traceability:`` followed by the need ID.

.. code-block:: python

	 # req-Id: TOOL_REQ__EXAMPLE_ID
	 # req-traceability: TOOL_REQ__EXAMPLE_ID

For an example, look at the attribute ``source_code_link``
of :need:`tool_req__docs_common_attr_title`.

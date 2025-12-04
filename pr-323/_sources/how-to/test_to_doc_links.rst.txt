Reference Docs in Tests
=======================

In tests, you want to reference requirements (needs).
The docs-as-code tool will create backlinks in the documentation.

Docs-as-code parses `test.xml` files produced by Bazel under `bazel-testlogs/`.
To attach metadata to tests use the project tooling decorator (provided by the
attribute plugin). Example usage:

.. code-block:: python

	 from attribute_plugin import add_test_properties

	 @add_test_properties(
			 partially_verifies=["tool_req__docs_common_attr_title", "tool_req__docs_common_attr_description"],
			 test_type="interface-test",
			 derivation_technique="boundary-values",
	 )
	 def test_feature():
			 """Short description of what the test does."""
			 ...

TestLink will extract test name, file, line, result and verification lists
(`PartiallyVerifies`, `FullyVerifies`) and create external needs from tests
and `testlink` attributes on requirements that reference the test.


Limitations
-----------

- Not compatible with Esbonio/Live_preview.
- Tags and XML must match the expected format exactly for parsing to work.
- Tests must be executed by Bazel first so `test.xml` files exist.

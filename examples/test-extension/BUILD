/**
 * This example demonstrates how to use the setup extension to access
 * transitive dependencies like score_python_basics.
 * 
 * In a real downstream project, you would have a MODULE.bazel like this:
 * 
 * ```starlark
 * module(name = "my_project", version = "1.0.0")
 * 
 * bazel_dep(name = "score_docs_as_code", version = "0.4.0")
 * 
 * # Use the setup extension to access transitive dependencies
 * use_extension("@score_docs_as_code//setup:setup.bzl", "setup")
 * use_repo(setup, "score_python_basics")
 * ```
 * 
 * Then in your BUILD file, you can use score_python_basics utilities:
 */

load("@score_python_basics//:defs.bzl", "score_py_pytest")

# This demonstrates that score_python_basics is available
# without explicitly declaring it as a bazel_dep
score_py_pytest(
    name = "test_extension_example",
    srcs = ["test_extension.py"],
)
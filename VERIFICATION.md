# Verification Steps for Setup Extension

This document outlines how to verify that the setup extension works correctly.

## Manual Testing Steps

### 1. Create a test downstream project

Create a new directory with the following structure:

```
test-downstream-project/
├── MODULE.bazel
├── BUILD
└── test.py
```

### 2. Add MODULE.bazel content

```starlark
module(name = "test_downstream", version = "1.0.0")

bazel_dep(name = "score_docs_as_code", version = "0.4.0")

# Use the setup extension to access transitive dependencies
use_extension("@score_docs_as_code//setup:setup.bzl", "setup")
use_repo(setup, "score_python_basics")
```

### 3. Add BUILD content

```starlark
load("@score_python_basics//:defs.bzl", "score_py_pytest")

score_py_pytest(
    name = "test",
    srcs = ["test.py"],
)
```

### 4. Add test.py content

```python
def test_works():
    assert True
```

### 5. Verify the build works

Run: `bazel test //:test`

If successful, this confirms that:
- The setup extension properly exposes score_python_basics
- Downstream projects don't need to manually declare score_python_basics
- The transitive dependency resolution works correctly

### 6. Verify documentation macro usage

Create a docs example in the test project:

```starlark
load("@score_docs_as_code//:docs.bzl", "docs")

docs(
    conf_dir = "docs",
    source_dir = "docs", 
    docs_targets = [{"suffix": ""}],
    source_files_to_scan_for_needs_links = [],
)
```

Run: `bazel run //:ide_support`

This should work without any additional dependencies since score_python_basics is available via the extension.

## Expected Behavior

- ✅ Projects can use the docs() macro without manually declaring score_python_basics
- ✅ Projects can use score_py_pytest and other utilities from score_python_basics
- ✅ Projects can use score_virtualenv for IDE support
- ✅ The extension follows Bazel best practices for modular dependencies
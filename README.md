# docs-as-code

Docs-as-code tooling for Eclipse S-CORE

## Overview

The S-CORE docs Sphinx configuration and build code.

## Usage

### Using the module in your Bazel project

To use `score_docs_as_code` in your Bazel project, add the following to your `MODULE.bazel`:

```starlark
bazel_dep(name = "score_docs_as_code", version = "...")

# Use the setup extension to access transitive dependencies
use_extension("@score_docs_as_code//setup:setup.bzl", "setup")
use_repo(setup, "score_python_basics")
```

This pattern allows you to use the `docs()` macro and other utilities without manually declaring all transitive dependencies like `score_python_basics` in your own `MODULE.bazel`.

## Building documentation

#### Run a documentation build:

#### Integrate latest score main branch

```bash
bazel run //docs:incremental_latest
```

#### Access your documentation at:

- `_build/` for incremental

#### Getting IDE support

Create the virtual environment via `bazel run //process:ide_support`.\
If your IDE does not automatically ask you to activate the newly created environment you can activate it.

- In VSCode via `ctrl+p` => `Select Python Interpreter` then select `.venv/bin/python`
- In the terminal via `source .venv/bin/activate`

#### Format your documentation with:

```bash
bazel test //src:format.check
bazel run //src:format.fix
```

#### Find & fix missing copyright

```bash
bazel run //:copyright-check
bazel run //:copyright.fix
```

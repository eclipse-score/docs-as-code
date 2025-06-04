# docs-as-code

Docs-as-code tooling for Eclipse S-CORE

## Overview

The S-CORE docs Sphinx configuration and build code.

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

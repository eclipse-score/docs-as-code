<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# Public `docs.bzl` scenario tests

These pytest tests exercise the public `docs()` and `docs_bundle()` macros
through real Bazel builds and runs. Fixtures live below `scenarios/`; the test
modules are `test_docs_bzl_scenarios.py` and
`test_expected_output_consistency.py`.

## Run

```sh
.venv_docs/bin/python -m pytest -vv src/tests/docs_bzl
```

The suite runs Bazel and should be run sequentially. CI splits it into:

```sh
.venv_docs/bin/python -m pytest -vv -m bazel_cached src/tests/docs_bzl
.venv_docs/bin/python -m pytest -vv -m bazel_slow src/tests/docs_bzl
```

Build-only expected outputs are marked `bazel_cached`; outputs that execute
Sphinx through `bazel run`, as well as expected-failure tests, are marked
`bazel_slow`.

## Expected outputs

Positive scenarios may check in files below a fixture's `_expected/` directory:

- `_expected/<target>/...` checks selected files below a directory output.
- `_expected/<target>.<suffix>` checks one file output.

Only files already present below `_expected/` are part of the contract. JSON is
compared as sorted, formatted data; other files, including HTML, are compared
byte-for-byte.

Each expected output is its own pytest case. When generated content changes,
the case updates the checked-in file, prints the unified diff through pytest,
and fails with exit code 1. Review the change and run pytest again; an
unchanged output passes. Files are never added or removed automatically.

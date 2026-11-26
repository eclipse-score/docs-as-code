<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# Public `docs.bzl` scenario tests

These pytest tests exercise the public `docs()` and `docs_bundle()` macros
through real Bazel builds and runs. The tests are the `test_*.py` files in this
directory. Fixtures live in two places:

- `scenarios/`: a separate Bazel module (`score_scenarios`) that uses
  docs-as-code through `@score_docs_as_code`, the way a real project does. It is
  listed in `.bazelignore`, and the tests run Bazel inside this directory. Add
  new scenarios here.
- `in_tree_scenarios/`: packages of docs-as-code itself. Only scenarios that
  docs-as-code's own `BUILD` mounts into its documentation live here.

`helpers.scenario_package()` finds a scenario in either place, so tests refer
to a scenario by its name only.

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

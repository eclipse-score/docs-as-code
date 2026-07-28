<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# End-to-end test for Bazel documentation mounts

This directory contains one black-box test for the public `docs_bundle()` and
`docs()` macros. It does not inspect a Starlark provider or the generated
mount manifest. Instead, it runs the same `:docs` executable that a user would
start with `bazel run` and asserts the visible Sphinx result.

Run the test with:

```console
bazel test //src/tests/mounts_contract:mount_docs_e2e_test
```

## Fixture

The fixture builds this small documentation site:

```text
host_docs/
└── concepts/index
    └── parent bundle at concepts/example_bundle
        └── child bundle at child
```

`docs_bundle()` defines the parent and child bundles. `docs()` defines the
synthetic host project and creates its ordinary `:docs` binary, just as it
does in a real project.

## Why the test starts a subprocess

`docs()` is a Starlark macro, not an executable function. During `bazel test`
Bazel evaluates the macro and creates targets, including this fixture's
`:docs` `py_binary`. It does not run that binary merely because the macro was
evaluated.

The Python test starts that already-built binary in a subprocess:

```text
docs() macro
    -> defines :docs
bazel test
    -> builds :docs and starts the pytest test
pytest subprocess
    -> executes :docs
    -> incremental.py runs Sphinx
    -> score_mounts configures sphinx-mounts
```

This is deliberately not a nested `bazel run`: a Bazel test must not start
another Bazel process in its sandbox. The subprocess directly executes the
`:docs` file that Bazel placed in the test runfiles.

## What the test verifies

`test_docs_build_mounts_bundle_and_extends_toctree` creates a writable
temporary workspace, runs the fixture's `:docs` binary, and checks:

- Sphinx reports that it extended the `concepts/index` toctree.
- The mounted document is rendered as
  `_build/concepts/example_bundle/index.html`.

Together these assertions cover bundle composition, the mount manifest,
runfiles path resolution, the Sphinx extension, the target Toctree, and HTML
output. A wrong `mount_at` or `attach_to` fails this test as a user would see
it: Sphinx cannot extend the expected Toctree or the mounted page is absent.

## Related tests

- `bazel test //src/extensions/score_mounts:score_mounts_tests` contains
  Python unit tests for the `score_mounts` extension.
- `bazel build //src/tests/mounts_conflict:bad`, `:bad_attach_to`, and
  `:bad_entry_doc` are manually invoked negative fixtures. They must fail
  because one source directory cannot produce conflicting mount locations,
  Toctree targets, or entry documents.
- `bazel run //:docs` remains the project-wide documentation smoke check.

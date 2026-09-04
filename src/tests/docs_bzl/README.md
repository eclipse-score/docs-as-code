<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# Public `docs.bzl` integration tests

These tests run **outside** Bazel with pytest and drive the public `docs.bzl`
macros through real `bazel run` / `bazel build` commands. They cover exactly
what a consumer invokes: `docs()`, `docs_bundle()`, mounts, cross-module
compatibility reporting, and failure cases.

```text
docs_bzl/
├── scenarios/       # one fixture per consumer scenario
│   ├── basic_docs/
│   ├── reference_integration/
│   ├── metamodel_violation/
│   ├── nested_bundles/
│   ├── subdirectory_bundle/
│   ├── external_bundle/
│   ├── local_version_mismatch/
│   └── invalid_bundle_placements/
└── test_<scenario>.py
```

Each scenario has a fixture folder and a matching pytest file. The names describe
consumer behavior, not the Bazel mechanism used to execute it. Positive rendering
uses `bazel run`; sandbox-only behavior uses `bazel build`; invalid package
definitions are expected build failures. Assertions retain rendered HTML,
manifest order and metadata, source links, toctree attachment, and diagnostics.
The cross-module compatibility test creates its consumer in a temporary
workspace, so this repository's production ``MODULE.bazel`` stays free of test
dependencies while the test still traverses real Bzlmod module boundaries.

Note that these tests run `bazel` commands, so they are slow. They need to be executed
sequentially. Use sparingly. They do not call `bazel clean`, so the persistent
Bazel server and its action, repository, and disk caches are reused between
cases. There is still a small analysis/startup cost per command; keep scenarios
coarse-grained and use `bazel run` only where runtime behavior matters.

Run via:

    .venv_docs/bin/python -m pytest -vv src/tests/docs_bzl

The suite is deliberately separate from `bazel test //...`, since pytest is its
driver. CI stores its JUnit XML together with the Bazel test reports.

Tests are marked according to whether their Bazel work can be reused from the
action cache. To run only the cacheable cases:

    .venv_docs/bin/python -m pytest -vv -m bazel_cached src/tests/docs_bzl

To run the runtime and expected-failure cases:

    .venv_docs/bin/python -m pytest -vv -m bazel_slow src/tests/docs_bzl

The CI workflow runs these two commands in that order, so the cacheable tests
provide the fast first feedback before the runtime tests start.

The default command above runs both groups. Golden scenarios are marked
automatically: scenarios with a `docs` expected output are `bazel_slow` cases;
scenarios containing only successful build outputs are `bazel_cached` cases.
Expected-failure tests are also `bazel_slow`, because failed analysis does not
produce reusable action outputs.

## Expected target outputs

Positive scenarios may check in direct output files below an `_expected`
directory next to their fixture. An `_expected/<target>` directory contains
expected files relative to that target's output root; an
`_expected/<target>.<suffix>` file checks one file output. Only files present
below an expected directory are compared, so unrelated Bazel or Sphinx output
is ignored.

For example:

```text
scenarios/basic_docs/
└── _expected/
    ├── docs/
    │   └── index.html
    ├── needs_json/
    │   └── needs.json
    └── generated_config.py
```

The short target names are mapped to their real Bazel labels and output roots in
`expected_outputs.py`; this also includes internal generated targets when their
output is part of the contract. JSON files are parsed and compared as
deterministically formatted, sorted JSON so that their checked-in form remains
readable. Other files, including HTML, are compared byte-for-byte; expected
files should therefore contain only deterministic output. Missing expected files
or changed content fail the test, while additional actual files do not.

To refresh the checked-in files after an intentional output change, run the
updater for one scenario:

    .venv_docs/bin/python -m src.tests.docs_bzl.expected_outputs --update basic_docs

The scenario argument uses the same path as pytest, for example
`reference_integration/modern_module`. Omitting it updates all scenarios:

    .venv_docs/bin/python -m src.tests.docs_bzl.expected_outputs --update

The updater only overwrites files that already exist below `_expected`; it does
not add every generated file or remove files. Review the resulting Git diff and
run the normal pytest suite afterwards. When updating all scenarios, their
build-only targets are grouped into one Bazel invocation; runtime targets still
run one at a time.

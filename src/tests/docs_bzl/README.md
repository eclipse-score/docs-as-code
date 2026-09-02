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

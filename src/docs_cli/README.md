<!--
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-License-Identifier: Apache-2.0
-->

# Documentation CLI

This package runs local documentation builds and live preview for the targets
created by [`docs()`](../../../docs.bzl). Bazel supplies the source files,
configuration, dependencies and environment for each invocation.

## Commands

Run these targets in the package that calls `docs()`. The examples assume the
workspace root; for a nested package, use a label such as `//component:docs`.

| Command | Action | Result |
| --- | --- | --- |
| `bazel run //:docs` | `incremental` | Build HTML, reusing existing Sphinx output where possible. |
| `bazel run //:docs_check` | `check` | Run the Sphinx `needs` builder. |
| `bazel run //:docs_link_check` | `linkcheck` | Run the Sphinx `linkcheck` builder. |
| `bazel run //:live_preview` | `live_preview` | Rebuild on edits and serve the documentation with sphinx-autobuild. |


## Layout and Bazel integration

- `cli.py` contains the complete implementation: CLI parsing, Sphinx arguments,
  cache checks, bundle watch directories and action dispatch.
- `dirty_build_test.py` covers cache invalidation and mounted watch directories.
- `main_test.py` covers dispatch, build results and the Bazel environment contract.

`_declare_docs_binary()` in `docs.bzl` creates a separate `py_binary` for each
command, using the exported `cli.py` directly as its source. Each binary receives
one `SCORE_DOCS_CONFIG` payload and its dependencies from `docs()`.

The `all_sources` filegroup is included by `//src:all_sources` so source-code
linking can traverse this Bazel package boundary.

## Configuration and build state

`SCORE_DOCS_CONFIG` is a versioned JSON object. Version `1` contains the action,
package/source/output/config paths, merged external Needs labels, testcase source
directories, and optional mounts, source-links, metamodel, known-good, and Needs
settings. A typical interactive payload looks like this:

```json
{
  "version": 1,
  "action": "incremental",
  "package_directory": "component",
  "source_directory": "docs",
  "output_directory": "_build",
  "config_file": "_main/component/docs/conf.py",
  "external_needs_sources": ["//other:needs_json"],
  "testcase_source_dirs": ["src/tests"],
  "mounts_manifest": "_main/component/_mounts_manifest.json",
  "source_links": "_main/component/sourcelinks_json.json",
  "metamodel": null,
  "known_good": null,
  "master_doc": null,
  "bundle_needs_export": null,
  "plain_links": null
}
```

Interactive paths are runfiles-relative and sandboxed Needs paths are
execution-root-relative; the CLI resolves both forms before invoking Sphinx.
`BUILD_WORKSPACE_DIRECTORY`, `RUNFILES_DIR`, `JAVA_RUNFILES`, and
`GITHUB_REPOSITORY` remain process environment because they describe runtime or
CI context rather than documentation-target configuration.

All actions share the package's `_build` directory. Before starting, the CLI
removes stale output if the previous build recorded warnings, the stored hash
is missing, or the contents of `MODULE.bazel`, `MODULE.bazel.lock` or the package's
`BUILD` file have changed. Successful non-preview builds record the input hash;
failed builds append a marker to `warnings.txt` to force cleanup next time.

Live preview also watches mounted bundle source directories and generated data
directories outside the main Sphinx source directory, using the same mount
resolver as the Sphinx extension.

## Tests

From the repository root:

```sh
bazel test //src/docs_cli:dirty_build_test //src/docs_cli:main_test
```

To exercise the entry script and its runfiles with an actual Sphinx build:

```sh
bazel run //src/tests/docs_bzl/scenarios/basic_docs:docs
```

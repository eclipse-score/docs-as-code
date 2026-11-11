<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# End-to-end tests for the public `docs.bzl` API

These tests use `docs()` and `docs_bundle()` the way a downstream S-CORE module
does: through real `bazel build` / `bazel run` commands in a separate Bazel
module that depends on `score_docs_as_code`.

```text
end_to_end/
  consumer/              consumer module (own MODULE.bazel, ignored by the root workspace)
    scenarios/<name>/    one Bazel package (or package tree) per scenario
  cross_module_fixture/  second local module for the cross-module tests
  testcases/             pytest: helpers, golden harness, test_<scenario>.py
```

## Run

```sh
.venv_docs/bin/python -m pytest -vv src/tests/end_to_end
```

The suite runs Bazel and must run sequentially. CI splits it with markers:

```sh
.venv_docs/bin/python -m pytest -vv -m bazel_cached src/tests/end_to_end
.venv_docs/bin/python -m pytest -vv -m bazel_slow src/tests/end_to_end
```

`bazel_cached` marks build-only checks. `bazel_slow` marks checks that run Sphinx
through `bazel run`, and expected-failure builds.

To try a scenario by hand, run Bazel from the consumer workspace:

```sh
cd src/tests/end_to_end/consumer
bazel run //scenarios/basic_docs:docs
```

## What is covered

| Scenario | Test module | What it protects |
| --- | --- | --- |
| `basic_docs` | `test_basic_docs.py` | Configuration only through `docs()` arguments (no `conf.py`); root `data` files |
| `data_files_runfiles` | `test_data_files_runfiles.py` | Generated pages in `srcs`, legacy `data` pages, explicit `srcs` selection |
| `nested_bundles` | `test_nested_bundles.py` | Bundles inside bundles: mount points, `toctree_index`, `data` ownership, transitive source links |
| `subdirectory_bundle` | `test_subdirectory_bundle.py` | Bundles in sub-packages, transitive Needs exactly once, checks across packages |
| `external_bundle` | `test_external_bundle.py` | Mounting a `docs_bundle` published by another module |
| `external_needs_inputs` | `test_external_needs_inputs.py` | `external_needs` from `docs()`, `docs_bundle()` and `needs_json_file` |
| `deprecated_needs_data` | `test_deprecated_needs_data.py` | Needs inventories passed through `data` |
| `root_docs_config` | `test_root_docs_config.py` | Configuration supplied by a root docs target |
| `coverage_summary`, `reference_integration` | `test_coverage_summary.py`, `test_coverage_report.py` | Coverage attribution and coverage pies |
| `invalid_bundle_placements`, `invalid_source_combination` | `test_invalid_bundle_placements.py` | Rejected bundle placements and source combinations |
| `metamodel_violation`, `missing_docs_config` | `test_metamodel_violation.py`, `test_missing_docs_config.py` | Errors with their specific message |
| `local_version_mismatch`, `cross_module_fixture` | `test_cross_module_compatibility.py` | Compatibility findings across a real module boundary |
| `reference_integration` | `test_reference_integration.py`, `test_golden_outputs.py` | A representative S-CORE composition: platform, legacy and modern modules, nested components |

## Add a test

1. **Pick the scenario.** Add to a focused scenario when the behavior fits one
   in the table above. Create a new small scenario under `consumer/scenarios/`
   for a new behavior. Extend `reference_integration` only when the question is
   about the combined S-CORE setup.
2. **Name the test after the behavior** it protects, e.g.
   `test_mount_without_attach_to_joins_the_root_toctree`. One behavior per test.
3. **Assert the specific facts:** a Need ID, a link target, a manifest entry,
   a file that must not exist. Expected failures must check the error message,
   not just the non-zero exit code.
4. **Share one build or render per scenario.** Use a module-scoped fixture
   (see `test_nested_bundles.py`) when several tests read the same output.
5. **Use the helpers** in `testcases/helpers.py` (`run_scenario`,
   `built_output`, `load_needs`, `toctree_links`) instead of hard-coding Bazel
   output paths.

## Golden samples (reference_integration only)

Golden samples are kept only for `reference_integration`. There, protecting
the whole generated output of a representative composition is intended. Do not
add `_expected/` directories to other scenarios; write a named assertion
instead.

Files below a package's `_expected/` directory are checked like this:

- `_expected/<target>/...` checks selected files below a directory output.
- `_expected/<target>.<suffix>` checks one file output.

`testcases/expected_outputs.py` maps each `<target>` name to its Bazel target.
Only files already present below `_expected/` are part of the contract. JSON is
compared as sorted, formatted data. Other files, including HTML, are compared
byte-for-byte after normalizing random Sphinx-Needs wrapper IDs and checkout
metadata in local source links.

### Reviewing a golden diff

When generated content changes, the test rewrites the checked-in file, prints
the unified diff and fails. Then:

1. Read the diff in the pytest output or with `git diff`.
2. If the change is intended, commit the updated files. The next run passes.
3. If it is not, fix the code and run `git checkout` on the rewritten files.

Files are never added or removed automatically.

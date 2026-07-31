<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Docs-As-Code Consumer Tests

# Testing

![test levels in S-CORE docs-as-code](test-levels.drawio.svg)

## end-to-end tests

*Also known as system, product, or black-box tests.*

This directory contains end-to-end tests at two scopes:

- `docs_bzl`: controlled integration scenarios for the public `docs.bzl` API:
  `docs()`, `docs_bundle()`, composition, invalid configurations, and external
  Bzlmod bundles. They run via plain pytest and issue the same real
  `bazel build` / `bazel run` commands a consumer uses. See
  [docs_bzl/README.md](docs_bzl/README.md) for layout and commands.

- `downstream_compatibility`: *(formerly consumer tests)* Tests local changes and Git-based overrides against real consumer repositories. This provides broad, intentionally less-controlled coverage and helps detect breaking changes in the docs-as-code system before they affect downstream consumers.

`bazel test //...` covers internal unit tests. It intentionally does not run
the public `docs_bzl` integration suite; CI and local contributors run that
suite explicitly through pytest.

### Bazel test targets

You can query targets in this directory with:

```bash
bazel query 'kind(".*_test", //src/tests/...)'
```

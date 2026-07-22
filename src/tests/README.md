<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# `docs()` end-to-end tests

*Also known as system, product, or black-box tests.*

This directory contains end-to-end tests for the public `docs()` macro. They exercise documentation builds through the public interface, rather than testing implementation details.

It contains:

- `docs_e2e`: A reusable baseline for end-to-end tests of the public `docs()` macro. It defines a minimal documentation project using `docs()`. The test starts the generated `:docs` binary, waits for Sphinx to produce the HTML output, and verifies that `_build/index.html` exists.

- `downstream_compatibility`: *(formerly consumer tests)* Tests local changes and Git-based overrides against real consumer repositories. This provides broad, intentionally less-controlled coverage and helps detect breaking changes in the docs-as-code system before they affect downstream consumers.

## Targets

You can query targets in this directory with:

```bash
bazel query 'kind(".*_test", //src/tests/...)'
```

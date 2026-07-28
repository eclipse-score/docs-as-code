<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# `docs()` end-to-end tests

These tests run **outside** Bazel with pytest and drive the public `docs()`
macro through real `bazel run` / `bazel build` commands against small fixture
packages in this directory. They test exactly what a user runs.

Note that these tests run `bazel` commands, so they are slow. They need to be executed
sequentially. Use sparingly.

Run via:

    pytest src/tests/docs_bzl -vv

*(no venv is required)*

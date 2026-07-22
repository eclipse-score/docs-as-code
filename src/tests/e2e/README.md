<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# Generic docs() end-to-end test

This package is the reusable baseline for end-to-end tests of the public
docs() macro.

Run:

    bazel test //src/tests/docs_e2e:basics

The fixture defines a minimal documentation project with docs(). The test
starts the resulting :docs binary, waits for Sphinx to build HTML, and checks
that _build/index.html exists.

support.py contains the common runner. It creates an isolated writable
workspace for the docs binary, copies the fixture source tree, supplies the
runtime environment, and preserves the runfiles layout required by Bazel.
Feature-specific tests should reuse this runner and add only their fixture data
and user-visible assertions.

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Bazel macro that chains ``bazel test`` (or ``bazel coverage``) with a
docs target in one command.

Usage in a consumer ``BUILD``::

    load("@score_docs_as_code//:bzl/docs_and_test.bzl", "docs_and_test")

    docs_and_test(
        name = "docs_full",
        test_targets = ["//score/..."],
    )

Generates two ``py_binary`` targets::

    bazel run //:docs_full           # tests/coverage, then //:docs
    bazel run //:docs_full_preview   # tests/coverage, then //:live_preview

Bazel itself has no mechanism to make a build target depend on the
execution of a test, so the orchestration lives outside the dependency
graph in a small Python driver shipped with this module.
"""

load("@rules_python//python:defs.bzl", "py_binary")

_DEFAULT_DRIVER = Label("@score_docs_as_code//:bzl/run_docs_and_test.py")

def _pipeline_binary(name, driver, test_targets, coverage, run_target, help_text):
    py_binary(
        name = name,
        srcs = [driver],
        main = driver,
        args = [
            "--tests",
            ",".join(test_targets),
            "--coverage" if coverage else "--no-coverage",
            "--docs",
            run_target,
        ],
        tags = ["cli_help=%s:\nbazel run //:%s" % (help_text, name)],
    )

def docs_and_test(
        name,
        test_targets,
        coverage = True,
        docs_target = "//:docs",
        preview_target = "//:live_preview",
        driver = None):
    """Create ``py_binary`` targets that run tests, then a docs command.

    Two targets are generated:

    * ``<name>``           — runs tests, then ``docs_target``.
    * ``<name>_preview``   — runs tests, then ``preview_target``
      (typically ``//:live_preview``).

    Coverage is on by default. When ``coverage = True`` the pipeline uses
    ``bazel coverage --combined_report=lcov`` on ``test_targets`` instead of
    plain ``bazel test``; that runs the same tests with LLVM/GCC coverage
    instrumentation and produces the aggregated LCOV at
    ``bazel-out/_coverage/_coverage_report.dat`` in a single rebuild.
    Targets without unit tests simply contribute no coverage data. Set
    ``coverage = False`` to fall back to plain ``bazel test`` (faster on
    first run, no LCOV).

    Extra Bazel CLI flags (e.g. ``--config=bl-x86_64-linux``) are not
    hard-coded in the ``BUILD`` file. Pass them on the command line after
    ``--``::

        bazel run //:docs_full -- \\
            --test-flag=--config=bl-x86_64-linux

    ``--test-flag`` is repeatable and forwarded to whichever underlying
    Bazel command runs (``test`` or ``coverage``).

    Args:
      name: Base target name; invoke with ``bazel run //:<name>`` or
        ``bazel run //:<name>_preview``.
      test_targets: Bazel labels/patterns for the test/coverage step
        (e.g. ``["//score/..."]``). Pass ``[]`` to skip.
      coverage: If ``True`` (default), replace ``bazel test`` with
        ``bazel coverage --combined_report=lcov`` so the docs build can
        pick up per-source-file LCOV data. If ``False``, run plain
        ``bazel test`` and produce no LCOV.
      docs_target: Label of the docs binary to invoke via ``bazel run``.
        Defaults to ``//:docs``.
      preview_target: Label of the live-preview binary to invoke via
        ``bazel run``. Defaults to ``//:live_preview``. Pass ``None`` to
        skip generating the preview target.
      driver: Label of the Python driver script. Defaults to the driver
        shipped with ``score_docs_as_code``; only override when you want
        to inject a custom driver.
    """
    driver = driver or _DEFAULT_DRIVER
    _pipeline_binary(
        name = name,
        driver = driver,
        test_targets = test_targets,
        coverage = coverage,
        run_target = docs_target,
        help_text = "Run tests, then build documentation",
    )

    if preview_target:
        _pipeline_binary(
            name = name + "_preview",
            driver = driver,
            test_targets = test_targets,
            coverage = coverage,
            run_target = preview_target,
            help_text = "Run tests, then start the docs live preview",
        )

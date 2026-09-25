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
"""Driver for the :bzl:`docs_and_test` macro.

Runs either ``bazel test`` or ``bazel coverage`` on the configured targets,
then ``bazel run`` on the docs target. Aborts the pipeline on the first
non-zero exit code so a failing step does not silently ship stale docs.

Extra Bazel CLI flags (typically ``--config=…``) are **not** baked into
the ``BUILD`` file; pass them at ``bazel run`` time after ``--``::

    bazel run //:docs_full -- \\
        --test-flag=--config=bl-x86_64-linux

``--test-flag`` is repeatable and forwarded to whichever underlying Bazel
command runs (``test`` or ``coverage``).

The script must be invoked from the workspace root — ``bazel run`` sets
``BUILD_WORKSPACE_DIRECTORY`` accordingly, so we chdir there before
invoking any nested Bazel commands.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def _split(csv: str) -> list[str]:
    return [x for x in csv.split(",") if x]


def _run(cmd: list[str]) -> None:
    print(f">>> {' '.join(cmd)}", flush=True)
    try:
        result = subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        # Ctrl+C hits both us and the child via the process group. The child
        # already exited with 130; propagate the same status without dumping
        # a Python traceback so `docs_full_preview` behaves like a bare
        # `bazel run //:live_preview`.
        sys.exit(130)
    if result.returncode != 0:
        print(
            f"!!! step failed with exit code {result.returncode}: {' '.join(cmd)}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tests",
        default="",
        help="Comma-separated Bazel labels/patterns for the test step. "
        "Empty string skips the step entirely.",
    )
    parser.add_argument(
        "--coverage",
        dest="coverage",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run 'bazel coverage --combined_report=lcov' instead of "
        "'bazel test' on --tests. Default: True.",
    )
    parser.add_argument(
        "--docs",
        required=True,
        help="Bazel label of the docs binary to invoke via 'bazel run'.",
    )
    parser.add_argument(
        "--test-flag",
        action="append",
        default=[],
        help="Extra CLI flag forwarded to the test/coverage step "
        "(repeatable). Typically '--config=…'.",
    )
    args = parser.parse_args()

    # `bazel run` sets BUILD_WORKSPACE_DIRECTORY to the workspace root; nested
    # bazel invocations must run from there so they see MODULE.bazel etc.
    workspace = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        os.chdir(workspace)

    test_targets = _split(args.tests)

    if test_targets:
        if args.coverage:
            _run(
                [
                    "bazel",
                    "coverage",
                    "--combined_report=lcov",
                    *args.test_flag,
                    "--",
                    *test_targets,
                ]
            )
        else:
            _run(["bazel", "test", *args.test_flag, "--", *test_targets])
    _run(["bazel", "run", args.docs])


if __name__ == "__main__":
    main()

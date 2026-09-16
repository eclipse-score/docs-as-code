# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
import sys
from typing import cast

import pytest
from python.runfiles import Runfiles


def _resolve_runfiles_paths(args: list[str]) -> list[str]:
    """Turn runfiles addresses in pytest arguments into filesystem paths."""
    runfiles = Runfiles.Create()
    if runfiles is None:
        return args

    resolved_args: list[str] = []
    for arg in args:
        # pytest flags and their ordinary values are not runfiles addresses.
        # rlocationpath values always include a repository and use `/` as the
        # separator, so only those path-like arguments need a lookup.
        if arg.startswith("-") or "=" in arg or "/" not in arg:
            resolved_args.append(arg)
            continue

        # pytest expects ordinary paths for its config and test-file arguments;
        # rlocationpath values also work with manifest-only runfiles layouts.
        try:
            resolved_path = cast(str | None, runfiles.Rlocation(arg))
            resolved_args.append(resolved_path or arg)
        except ValueError:
            # Preserve non-normalized user arguments; only Bazel's generated
            # rlocationpath spellings are guaranteed to be normalized.
            resolved_args.append(arg)
    return resolved_args


def main(argv: list[str] | None = None) -> int:
    """Run pytest after resolving any Bazel runfiles arguments."""
    if argv is None:
        argv = sys.argv[1:]
    return pytest.main(_resolve_runfiles_paths(argv))


if __name__ == "__main__":
    sys.exit(main())

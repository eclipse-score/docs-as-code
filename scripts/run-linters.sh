#!/usr/bin/env bash
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
set -euo pipefail

bazel run //:ide_support

echo "Running Ruff linter..."
bazel run @score_tooling//tools:ruff check

echo "Running basedpyright..."
.venv_docs/bin/python3 -m basedpyright

echo "Running Actionlint..."
bazel run @score_tooling//tools:actionlint

echo "Running Shellcheck..."
# SC2038: find/xargs pattern works fine here despite non-alphanumeric filename warning
#         The recommended -print0 | xargs -0 solution causes:
#         "openBinaryFile: does not exist" with bazel run
# shellcheck disable=SC2038
find . \
  -type d \( -name .git -o -name .venv -o -name bazel-out -o -name node_modules \) -prune -false \
  -o -type f -exec grep -Il '^#!.*sh' {} \; | \
# SC1128: Shebang after copyright header is intentional
xargs bazel run @score_tooling//tools:shellcheck -- --exclude=SC1128

echo "Running Yamlfmt..."
bazel run @score_tooling//tools:yamlfmt -- "$(find . \
  -type d \( -name .git -o -name .venv -o -name bazel-out -o -name node_modules \) -prune -false \
  -o -type f \( -name "*.yaml" -o -name "*.yml" \) | tr '\n' '\0' | xargs -0)"

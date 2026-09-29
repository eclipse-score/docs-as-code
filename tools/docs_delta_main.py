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
"""Bazel launcher for the docs-delta CLI package."""

from tools.docs_delta.cli import main

if __name__ == "__main__":  # pragma: no cover - exercised via the Bazel binary
    raise SystemExit(main())

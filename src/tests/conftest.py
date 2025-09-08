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
import pytest


def pytest_addoption(parser: pytest.Parser):
    """Add custom command line options to pytest"""
    parser.addoption(
        "--repo",
        action="store",
        default=None,
        help="Comma separated string of ConsumerRepo's name tests to run",
    )
    parser.addoption(
        "--disable-cache",
        action="store_true",
        default=False,
        help="Disable local caching",
    )

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

import os

project = "Metamodel Check"
project_url = "https://example.invalid/metamodel-check"
extensions = ["score_sphinx_bundle"]

# NOTE: docs(metamodel=...) does not reach the :needs_json (sphinx_docs) target
# in the current docs.bzl (the metamodel_opts/metamodel_data wiring was dropped
# in commit 970f2604 / #484). We therefore load the custom metamodel via the
# officially-supported score_metamodel_yaml config value. The YAML lives next to
# this conf.py so it is globbed into :docs_sources and materialized in the sandbox.
score_metamodel_yaml = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "metamodel.yaml"
)

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

project = "External Needs Producer"
project_url = "https://example.invalid/external-needs-producer"
extensions = ["score_sphinx_bundle"]

# sphinx-needs writes this as the needs.json `current_version`. A consumer that
# mounts this needs.json resolves needs under this version key, so it must be
# non-empty (an unset version yields an empty current_version that sphinx-needs
# rejects with "No version defined").
version = "main"

# docs(metamodel=...) does not reach the :needs_json (sphinx_docs) target in the
# current docs.bzl, so we load the custom metamodel via the officially-supported
# score_metamodel_yaml config value. The YAML lives next to this conf.py so it is
# globbed into :docs_sources and materialized in the sandbox.
score_metamodel_yaml = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "metamodel.yaml"
)

# The producer need id `test_req__producer__demo` has three "__"-parts. The
# id_contains_feature check requires the feature part ("producer") to appear in
# the docname or in required_in_id; the fixture lives in index.rst, so we declare
# it here.
required_in_id = ["producer"]

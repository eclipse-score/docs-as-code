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

project = "External Needs Consumer"
project_url = "https://example.invalid/external-needs-consumer"
extensions = ["score_sphinx_bundle"]

# FIXME:
# sphinx-needs refuses to add an external need whose type is not registered in
# this project's needs_types, so the consumer must declare the producer's
# `test_req` type. score_metamodel's own checks skip external needs, so the
# id/parts rules never run here. Loaded via the score_metamodel_yaml config
# value because docs(metamodel=...) does not reach the build target.
score_metamodel_yaml = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "metamodel.yaml"
)

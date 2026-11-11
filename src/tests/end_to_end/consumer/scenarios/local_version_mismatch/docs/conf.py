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

project = "Local version mismatch"
project_url = "https://example.invalid/local-version-mismatch"
extensions = ["score_sphinx_bundle"]
score_metamodel_yaml = os.path.join(os.path.dirname(__file__), "metamodel.yaml")
required_in_id = ["local"]

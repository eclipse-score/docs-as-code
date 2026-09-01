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

project = "SCORE upward bundle example"
project_url = "https://example.invalid/upward-bundles"
version = "0.0.0"

extensions = ["score_sphinx_bundle"]

# The module's feature requirement lives in module/index.rst. Its meaningful
# ID part is `module`, not the rebased docname `index`.
required_in_id = ["module"]

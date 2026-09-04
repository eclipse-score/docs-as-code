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
# Default Sphinx configuration emitted by the ``docs()`` macro and by
# standalone bundle-local Needs exports. SCORE Docs-as-Code owns these
# baseline settings. Project builds and the root bundle may provide their own
# conf.py; standalone bundle-local exports use this baseline.

project = {PROJECT}
project_url = {PROJECT_URL}
version = "0.0.0"

# Allow feature IDs that use the Bazel module name without its first
# underscore-separated prefix (for example, ``score_docs_as_code`` becomes
# ``docs_as_code``). A user-provided conf.py remains authoritative for the
# normal project build.
required_in_id = {REQUIRED_IN_ID}

extensions = ["score_sphinx_bundle"]

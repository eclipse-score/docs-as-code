<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

---
applyTo: "docs/requirements/requirements.rst"
---

This file contains docs-as-code requirements which derived from upstream process requirements.
Those are specified in `bazel-out/k8-fastbuild/bin/external/score_process+/needs_json/_build/needs/needs.json`

The docs-as-code requirements are implemented in this repository, most notably in `src/extensions/score_metamodel/metamodel.yaml`
The metamodel has references to docs-as-code requirement ids.

Ensure all of that is consistent.

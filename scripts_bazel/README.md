<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Scripts Bazel

This folder contains executables to be used within Bazel rules.

## `merge_needs_json`

Merge one or more Sphinx-Needs inventories while keeping the top-level
metadata and version container from the first input:

```text
bazel run //scripts_bazel:merge_needs_json -- \
  --output bazel-bin/merged-needs.json \
  path/to/needs-a.json path/to/needs-b.json
```

Each input must contain exactly one `versions` entry and an object-valued
`needs` field. Identical Need IDs are accepted only when their complete
objects match; conflicting definitions fail the command. The output is
written atomically, so an existing result is preserved when validation or
serialization fails.

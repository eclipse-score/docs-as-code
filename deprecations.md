<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Deprecated behavior to remove

This file tracks compatibility paths that should be removed after callers have
migrated to the current bundle model.

## Generated documentation declared through `data`

`docs_bundle(data = [...])` is still accepted for generated documentation
files, and `score_mounts` turns those files into runtime mounts. Generated
documentation should be declared with `docs_bundle(srcs = [...])` instead.

Once callers have migrated, remove the data-to-mount path from
`src/extensions/score_mounts/__init__.py` and the corresponding regression
fixture for `legacy_data_bundle`.

## External Needs passed through `docs(data = [...])`

Passing `needs_json` targets through `docs(data = [...])` is the old external
Needs interface. Callers should use `docs(external_needs = [...])` instead.

Once module repositories have migrated, remove the `needs_json` detection and
filtering in `docs.bzl`, together with the compatibility coverage for the old
`data` form.

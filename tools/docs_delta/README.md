<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Documentation Delta

Compare the Sphinx-Needs inventory and rendered HTML from two documentation
builds, then write a Markdown report. The command uses only the Python standard
library.

Run the CLI from the repository root with:

```sh
uv run --locked --project tools/docs_delta docs-delta --help
```

For a local comparison, provide the baseline and current build directories and
the URLs that reviewers should open:

```sh
uv run --locked --project tools/docs_delta docs-delta \
  --baseline-dir /path/to/baseline \
  --current-dir /path/to/current \
  --base-url https://example.org/docs/main \
  --pr-url https://example.org/docs/pr-123
```

In GitHub pull-request Actions, the CLI can resolve the baseline from a local,
full-history `gh-pages` checkout and derive the preview URLs from Actions
metadata. `docs-delta --help` lists the options for overriding those defaults.

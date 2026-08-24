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

## `needs_to_lobster`

Converts a sphinx-needs `needs.json` into a LOBSTER `lobster-req-trace`
(`.lobster`) file so sphinx-needs requirements can be aggregated with the
code/test `.lobster` artifacts by the LOBSTER CLI (`lobster-report` /
`lobster-ci-report`). Authoring (RST) and rendering (sphinx-needs dashboards)
are untouched; LOBSTER only sits downstream of `needs.json`.

```console
bazel run //scripts_bazel:needs_to_lobster -- \
    --needs-json _build/needs.json \
    --output tool_reqs.lobster \
    --types tool_req \
    --up-links satisfies
```

Under `bazel run` the process working directory is the runfiles tree, so
relative `--needs-json` / `--output` paths are resolved against
`$BUILD_WORKING_DIRECTORY` (the directory you invoked `bazel run` from), not the
sandbox. Absolute paths are always used as-is.

The `satisfies` links (e.g. `tool_req__* -> gd_req__*`) are emitted as LOBSTER
`refs`, so the process-requirement <-> tool-requirement relationship authored in
RST is preserved as a LOBSTER up-trace. Model the two sides as separate
requirement levels in a LOBSTER tracing policy (`Tool Requirements` `trace to:`
`Process Requirements`). A ready-to-run example policy is provided in
[`lobster.conf.example`](./lobster.conf.example):

```console
python3 scripts_bazel/needs_to_lobster.py --needs-json _build/needs.json --types tool_req --output tool_reqs.lobster
python3 scripts_bazel/needs_to_lobster.py --needs-json _build/needs.json --types gd_req  --output process_reqs.lobster
lobster-report --lobster-config=scripts_bazel/lobster.conf.example --out=report.json
lobster-ci-report report.json
```

The tracing policy is intentionally *not* owned by this converter; long term it
should live centrally (e.g. next to the `rules_score` `*.conf.tpl` templates),
so it is not duplicated per module.

Licensing: LOBSTER is AGPLv3. This tool never imports LOBSTER; it writes the
documented JSON schema and is consumed by the LOBSTER CLI as an external
process, keeping the Apache-2.0 code at arm's length.

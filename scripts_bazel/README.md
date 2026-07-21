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

The `satisfies` links (e.g. `tool_req__* -> gd_req__*`) are emitted as LOBSTER
`refs`, so the process-requirement <-> tool-requirement relationship authored in
RST is preserved as a LOBSTER up-trace. Model the two sides as separate
requirement levels in `lobster.conf` (`Tool Requirements` `trace to:`
`Process Requirements`).

Licensing: LOBSTER is AGPLv3. This tool never imports LOBSTER; it writes the
documented JSON schema and is consumed by the LOBSTER CLI as an external
process, keeping the Apache-2.0 code at arm's length.

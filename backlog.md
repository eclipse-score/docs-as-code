<!--
  *******************************************************************************
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
  *******************************************************************************
-->

# Backlog: upstream/main integration and `upward_bundles`

Last updated: 2026-08-28

## Current state

The local `upward_bundle` branch is based on `upstream/main` at `298732e4`.
The WIP integration is secured in commits `9eba2304` and `1a16863c` and has
been force-updated to `upstream/upward_bundle`. The working tree is clean; no
staged changes remain.

The final WIP delta is currently 33 files with approximately 1,947 additions
and 42 deletions. It is a working integration result, not yet a reviewable PR.

Verification completed before the split:

```text
bazel test //...                                      21/21 passed
.venv_docs/bin/python -m pytest -q src/tests/docs_bzl 28 passed
```

The full pre-commit hook also passed after the final formatting fix.

## Topics contained in the staged delta

### 1. Bundle-local Needs and bundle ownership

`docs_bundle` now distinguishes a bundle's own sources and data from nested
bundle content. It creates a local Needs export for the bundle's own sources,
with generated configuration, source-code links, selected metamodel, and the
correct `entry_doc` as Sphinx master document.

Relevant implementation files:

- `bzl/bundle_rules.bzl`
- `docs.bzl`
- `bundle_needs_conf.py.tpl`
- root `BUILD`

### 2. Hierarchical Needs via `upward_bundles`

The bundle provider carries direct and transitive upward dependencies. A
bundle can export its own Needs together with explicitly declared ancestors;
source-less hierarchy groups, multiple parents, diamond-shaped graphs, and
cyclic declarations are covered.

The top-level `docs()` macro receives the same hierarchy and exposes the
stable public `docs_source_bundle` and
`docs_source_bundle_needs_upward` targets. Downward `bundles` composition and
upward Needs interfaces remain separate concepts.

### 3. Cross-module external Needs

External Needs loading understands named `*_needs_upward` exports and their
namespaced runfiles paths. The consumer documentation project's
`project_url` is registered early enough and is used as the canonical base
URL for imported Needs.

This is covered by the cross-module fixture and the compatibility integration
tests.

### 4. Documentation and examples

The staged documentation explains the ownership model, hierarchy contract,
build graph, generated targets, and usage of `upward_bundles`:

- `docs/concepts/hierarchical_bundle_needs.md`
- `docs/how-to/upward_bundles.rst`
- `docs/reference/bazel_macros.rst`

The Mermaid-fence handling in `score_sphinx_bundle` supports the diagrams in
the Markdown documentation. It should remain only if the documentation PR
needs it and has a rendering regression test.

## Proposed PR plan

The PRs should be stacked on `upstream/main` in this order. Test fixtures and
tests belong with the feature they verify; the documentation is intentionally
separate from the implementation review.

### PR 1 — `docs_bundle`: local Needs and hierarchical `upward_bundles`

Approximate size: 900–1,100 LOC including focused tests.

Include:

- direct bundle ownership metadata and `bundle_own_files`;
- bundle-local `*_needs_local` and merged `*_needs_upward` exports;
- `upward_bundles` on `docs_bundle` and `docs()`;
- source-less hierarchy groups and transitive parent propagation;
- stable source-bundle aliases;
- cycle, multiple-parent, diamond, and local-versus-upward tests;
- Sphinx sandbox-safe metamodel inputs and `entry_doc` handling.

This is the main implementation PR. Keep the core hierarchy documentation
out of this PR except for concise API comments and test descriptions.

### PR 2 — Cross-module external Needs and URL semantics

Approximate size: 200–250 LOC including tests.

Include:

- parsing and resolving named `*_needs_upward` exports;
- consumer-owned canonical `project_url` handling;
- cross-module fixture and compatibility tests.

This PR depends on PR 1 because it consumes the generated upward export
targets.

### PR 3 — Documentation for hierarchical bundles

Approximate size: 700 LOC, mostly documentation.

Include:

- the hierarchy concept document;
- the `upward_bundles` How-to;
- the Bazel macro reference updates;
- Mermaid-fence support if required by the new Markdown diagrams, together
  with a small rendering test.

## Cleanup before creating the PRs

Remove or split out the following from the current staged integration:

- Mermaid-fence support unless it is required by the documentation PR and is
  covered by a regression test.

Keep this file as the planning record, but do not mix the planning backlog into
the implementation PRs unless repository policy requires it.

## Open follow-ups

These points are not blockers for the first hierarchy PR and should become
separate issues if they remain relevant after review:

- add a black-box test proving that a bundle-local export cannot see a sibling
  or descendant without an explicit upward dependency;
- define a negative test for missing or malformed upward export files;
- define custom-metamodel behavior when an imported Need type is absent from
  the consumer schema;
- specify duplicate-ID and URL behavior when a bundle is mounted downward and
  consumed upward at the same time;
- review generated target visibility and public naming across repositories;
- add release notes once the API is approved.

## Architecture contract to preserve

```text
child local Needs export
        │
        └── depends upward on explicit parent exports

parent public composed bundle
        └── mounts child documentation downward
```

Bundle-local exports contain no consumer mount paths. Mount paths, backlinks,
global checks, metrics, and final rendered output are resolved only by the
composed host documentation build.

`bundles` describes downward documentation composition. `upward_bundles`
describes the explicit Needs interface available to a bundle's own validation.

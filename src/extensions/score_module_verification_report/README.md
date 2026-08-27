<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# `score_module_verification_report`

Per-module verification report pages whose sections behave like ordinary RST.

Resolves [#764](https://github.com/eclipse-score/docs-as-code/issues/764) — option **K**.

## The governing design rule

> **The extension emits RST. It never reads the Need model to compute an answer.**

Rendering, not resolving. The directive emits `needtable` filters and `:need:`
references; sphinx-needs resolves all of them after collection, with its own
semantics, its own external-need handling and its own backlinks. The extension
therefore needs no `NeedsView`, no build lifecycle hook and no model
completeness at read time. The only thing it knows at read time is *which
sections exist*.

**Test for future changes:** if adding report content requires new Python that
walks needs and computes something, the line has been crossed. If it requires a
new `needtable` filter in the template, it has not.

## Authoring surface

One Need per module. That is the whole consumer-facing API:

```rst
.. mod_ver_report:: Baselibs Verification Report
   :id: mod_vrep__baselibs
   :belongs_to: mod__baselibs
   :covers: comp__baselibs_json, comp__baselibs_bit_manipulation
   :safety: ASIL_B
   :security: NO
   :status: valid
   :verification_method: test
   :titles:
      comp__baselibs_json = JSON Utilities

   Free-form introduction; becomes the Need's description.
```

Scaling to N modules = adding N Needs. Nothing else.

`:covers:` and `:belongs_to:` are **real link fields on the Need**, not opaque
directive options. That is what lets the metamodel validate them, generate
backlinks for free and report through the normal warning pipeline — and it is
why this extension owns no consistency-checking code. The feature the
statistics are about is derived from the module (`mod__x` → `feat__x`), exactly
as the upstream template does it; it feeds an `id == ...` filter, so the worst
case is an empty feature table.

`:titles:` is the only option that does not reach the Need: `component id =
Heading`, one per line. Without it the heading is derived from the id
(`comp__baselibs_json` → "Baselibs Json") — a deliberate last-resort fallback;
the real title is resolved by sphinx-needs in the component table.

## What gets emitted

A `mod_ver_report` Need followed by a **flat** list of sections. The content
follows the standard module verification report (the upstream
`mod_ver_report_tiny.need` template):

| Section | Content |
| ------- | ------- |
| Feature | `needtable` on the verified feature |
| Feature Requirements Statistics | status + test-coverage `needpie`, plus a requirements `needtable` in a dropdown |
| Feature Architecture Statistics | status + inspection `needpie`, plus an elements `needtable` |
| Feature Inspection Statistics | work products and the documents realising them |
| Component Overview | `needtable` over the covered components |
| *one per component* | component table, requirements + architecture statistics, requirements traceability, test coverage, architectural elements, and verification/safety-analysis documents |

Inside a component section the sub-parts stay `rubric` directives. Constraint 3
says no subsection nesting is needed, and nothing below a component level needs
its own anchor.

Every section is preceded by an explicit target namespaced with the report id
(`mod_vrep__baselibs__comp__baselibs_json`), so anchors are stable across
rebuilds and two reports on one page never collide.

## The report body is a template

[`src/needs_templates/mod_ver_report.need`](../../needs_templates/mod_ver_report.need)
holds the whole report. It is a Sphinx-Needs template file — `.need` extension,
living in `needs_template_folder` next to every other need template in this
repository. `setup()` sets `needs_template_folder` to the shipped folder unless
the project set it itself.

It is rendered by the **directive**, not by Sphinx-Needs' `:template:` option.
That difference is load-bearing: `:template:` renders into the Need's content,
which Sphinx-Needs parses with `match_titles=False`, so headings written there
can never become sections. The directive renders the file with a context built
only from the directive's options and from configuration, and returns the parsed
result into the surrounding document.

Changing what a report *says* means editing the template, not Python. A project
overrides it by dropping its own `mod_ver_report.need` into its
`needs_template_folder`; that folder is searched first and the shipped one is
the fallback, so a project template folder that does not contain the file still
builds.

The whole context is `report_id`, `module_id`, `module_slug`, `feature_id` and
`components` (each with `id`, `title` and `slug`), plus a `q` filter that safely
quotes a need id for a filter string. Column lists, table filters, the
work-product rows and the section list all live in the template — the extension
has **no configuration values of its own**.

### Differences from the upstream `.need` template

The upstream template is a sphinx-needs `.need` template, rendered *inside* the
Need node. Two changes were required:

- **Top-level `rubric` directives became sections.** A rubric looks like a
  heading and is nothing like one: no anchor, no ToC entry, no `:ref:` target,
  no search-index entry, and nothing at all in non-HTML builders. This is the
  entire point of the approach.
- **`linked_needs(module_id, "includes")` is gone.** Reading the Need graph
  while rendering is what forces the second read pass with its silent-failure
  mode. The component list comes from the report's own `covers` link field; the
  metamodel check enforces that it matches the module's `includes`.

## Two things that look like implementation details but are not

**1. The report body is a *sibling* of the Need, never its child.**

Sphinx turns headings into `section` nodes exactly once, during the read phase.
Sections are what produce anchors, sidebar entries, `:ref:` targets,
search-index entries and PDF bookmarks. sphinx-needs parses Need content with
`match_titles=False`, so a heading inside a `.need` template can never become a
section. The directive therefore parses its generated RST with
`parse_text_to_nodes(..., allow_section_headings=True)` and returns the nodes
into the surrounding document.

Moving the body inside the Need node — to make it render in the Need's box —
silently removes every section from the document and cannot be spotted by
looking at the HTML. Don't.

**2. The extension owns no build lifecycle.**

No `env-updated` re-read, no `build-finished` consistency pass, no
`env.*_registry` merged across parallel workers. `setup()` declares config
values and registers directives.

There is exactly one `config-inited` handler and it calls `add_directive`
twice — directive registration is last-one-wins and sphinx-needs registers
`mod_ver_report` from its own `config-inited` handler. It touches no
environment state and reads no needs.
`tests/test_report_integration.py` asserts this stays true.

## Validation lives in the metamodel

`src/extensions/score_metamodel/checks/mod_ver_report.py` enforces the rule with
real content: **every component in `mod__x.includes` must appear in the report's
`:covers:`, and vice versa** — bidirectional, so an omitted component is caught
as well as an over-claimed one.

Failure mode by design: drift is **detected, never silently corrected**.
Sections must exist at read time, so the list must be authored. The build fails
and someone edits one line.

Everything else — mandatory fields, allowed link targets — is already declared
in `metamodel.yaml` under `mod_ver_report`.

## Status

Proof of concept. Known gaps:

- **Work-product documents are matched by id substring.** `document` needs carry
  no link to the component they belong to, so the template's `document_filter`
  macro falls back to `{slug} in id.replace("_", "").lower()`. This *will*
  produce false positives (`json` also matches `jsonschema`). It is a filter in
  a template, not hand-written Python — replace it as soon as the metamodel
  models the link.
- **LCOV coverage is not integrated.** Reading a coverage report during
  directive execution introduces an untracked Sphinx dependency and breaks
  incremental correctness and Bazel reproducibility. The section renders a note
  saying so.
- `:covers:` is still `ANY` in `metamodel.yaml`; narrowing the allowed target
  types is a separate, consumer-affecting change.
- Two reports placed at *different* heading depths on one page rely on docutils'
  title-style bookkeeping and are untested.

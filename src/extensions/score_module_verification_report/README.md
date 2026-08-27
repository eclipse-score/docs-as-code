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

`:covers:` is a **real link field on the Need**, not an opaque directive option.
That is what lets the metamodel validate it, generate `covers_back` for free and
report through the normal warning pipeline — and it is why this extension owns
no consistency-checking code.

`:titles:` is the only presentation-only option: an optional `id = Heading` per
line. Without it the heading is derived from the id
(`comp__baselibs_json` → "Baselibs Json"), which is a deliberate last-resort
fallback — the *real* title is rendered by the `:need:` reference inside the
section, resolved by sphinx-needs.

## What gets emitted

A `mod_ver_report` Need followed by a flat list of sections:

| Section                | Content                                                     |
| ---------------------- | ----------------------------------------------------------- |
| Report Metadata        | `needtable` on the report itself                              |
| Verification Scope     | `needtable` over the covered components                       |
| *one per component*    | `:need:` reference plus a `needtable` of related needs        |
| Verification Evidence  | `needtable` over the report's `contains` / `evidence` backlinks |

Every section is preceded by an explicit target namespaced with the report id
(`mod_vrep__baselibs__comp__baselibs_json`), so anchors are stable across
rebuilds and two reports on one page never collide.

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

## Configuration

| Value                                  | Default                                                    |
| -------------------------------------- | ---------------------------------------------------------- |
| `mod_ver_report_metadata_columns`      | `id;title;status;safety;security;verification_method`        |
| `mod_ver_report_scope_columns`         | `id;title;type;status;safety;security`                       |
| `mod_ver_report_component_columns`     | `id;title;type;status`                                       |
| `mod_ver_report_component_filter`      | `id == {component_id} or {component_id} in belongs_to`       |
| `mod_ver_report_evidence_links`        | `["contains", "evidence"]`                                   |
| `mod_ver_report_evidence_columns`      | `id;title;type;status`                                       |

`{component_id}` is substituted with the *safely quoted* need id. Need ids are
matched against an allow-list before they reach any filter string; anything else
is warned about and skipped.

## Status

Proof of concept. Known gaps:

- `:covers:` is still `ANY` in `metamodel.yaml`; narrowing the allowed target
  types is a separate, consumer-affecting change.
- Two reports placed at *different* heading depths on one page rely on docutils'
  title-style bookkeeping and are untested.
- No `needflow` / `needpie` in the default template — both are pure additions to
  the templates when wanted.

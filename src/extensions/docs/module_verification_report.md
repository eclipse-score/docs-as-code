<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

(module-verification-report)=
# Module Verification Report

Give a module a verification report page by writing **one Need**. The report's
sections are ordinary RST sections: they appear in the sidebar and the local
ToC, they are `:ref:`-able from other pages, they land in the search index, and
they survive into non-HTML builders.

---

## Authoring

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

   Free-form introduction. It becomes the Need's description.
```

Scaling to N modules means adding N Needs — nothing else.

### Options

| Option | Meaning |
| ------ | ------- |
| *argument* | Report title. |
| `:id:` | Report Need id. Mandatory; also namespaces every generated anchor. |
| `:belongs_to:` | The module this report is about. |
| `:covers:` | The components in scope. A **real link field**, comma and/or whitespace separated. |
| `:titles:` | Heading for each component section, one `component id = Heading` per line. The only option that does not reach the Need. |
| *anything else* | Forwarded verbatim to the Need. The metamodel decides what is valid. |

Everything except `:titles:` ends up on the Need, so `covers_back` and the usual
link validation come for free. The feature the statistics are about is derived
from the module (`mod__x` → `feat__x`).

### Generated sections

A flat list, in this order:

1. **Feature** — the verified feature.
2. **Feature Requirements Statistics** — status and test-coverage pie charts
   plus a requirements table.
3. **Feature Architecture Statistics** — status and inspection pie charts plus
   an architecture elements table.
4. **Feature Inspection Statistics** — feature-level work products and the
   documents realising them.
5. **Component Overview** — the covered components.
6. **One section per covered component** — component table, requirements and
   architecture statistics, requirements traceability, test coverage,
   architectural elements, and verification/safety-analysis documents.

Inside a component section, the sub-parts are `rubric` directives rather than
sub-sections: no navigation is needed below the component level, and a flat list
keeps the sidebar readable.

Every number on the page comes out of a `needtable` or `needpie` filter that
sphinx-needs evaluates after need collection. The extension computes none of
them.

### Changing what a report says

The body is a Jinja template, not Python. It is a Sphinx-Needs template file
(`mod_ver_report.need`) and lives in `needs_template_folder` alongside every
other need template; the extension sets that config to the folder shipped with
Docs-as-Code unless your `conf.py` already set it.

To change the report, put your own `mod_ver_report.need` into your template
folder:

```python
needs_template_folder = "docs/_needs_templates"
```

Your folder is searched first and the shipped one is the fallback, so a folder
without the file still builds. The file is rendered by the directive rather
than by Sphinx-Needs' `:template:` option — `:template:` renders into the
Need's content, where headings can never become sections.

Anchors are namespaced with the report id, e.g.

```rst
See :ref:`mod_vrep__baselibs__comp__baselibs_json`.
```

so they are stable across rebuilds and two reports on one page never collide.

---

## Why the component list has to be written out

Sphinx turns headings into sections exactly once, during the read phase, before
the Need graph exists. A report cannot therefore discover its own components
from the graph and still get real sections — the two happen at different times.

So the list is authored, and drift is **detected rather than silently
corrected**: the metamodel check
`check_mod_ver_report_scope` compares the report's `:covers:` against the
module's `includes` in **both** directions and fails the build if they differ.
The fix is always a one-line edit.

---

## Design rule for contributors

> The extension emits RST. It never reads the Need model to compute an answer.

The directive emits `needtable` filters and `:need:` references; sphinx-needs
resolves them after collection. That is why the extension has no `NeedsView`, no
registry, no `build-finished` pass and no build lifecycle hooks at all.

If new report content needs Python that walks needs and computes something, the
line has been crossed. If it needs a new `needtable` filter in the template, it
has not.

This is also why the template does not use the upstream `linked_needs()` render
helper to discover components: that reads the Need graph during rendering, which
is what forces a second read pass.

Two invariants are enforced by tests and must not be "cleaned up":

- **The report body is a sibling of the Need, not its child.** sphinx-needs
  parses Need content with `match_titles=False`; moving the body inside the Need
  node silently removes every section, and the HTML still looks fine.
- **`setup()` registers directives and nothing else.** The single
  `config-inited` handler exists only because directive registration is
  last-one-wins.

See `src/extensions/score_module_verification_report/README.md` for the
configuration values and the full rationale.

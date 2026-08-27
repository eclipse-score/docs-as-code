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
| `:titles:` | Optional presentation-only heading overrides, one `id = Heading` per line. |
| *anything else* | Forwarded verbatim to the Need. The metamodel decides what is valid. |

Everything except `:titles:` ends up on the Need, so `covers_back` and the usual
link validation come for free.

### Generated sections

1. **Report Metadata** — the report's own fields.
2. **Verification Scope** — the covered components.
3. **One section per covered component** — a `:need:` reference plus a table of
   everything related to it.
4. **Verification Evidence** — whatever links to the report via `contains` or
   `evidence`.

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
line has been crossed. If it needs a new `needtable` filter, it has not.

Two invariants are enforced by tests and must not be "cleaned up":

- **The report body is a sibling of the Need, not its child.** sphinx-needs
  parses Need content with `match_titles=False`; moving the body inside the Need
  node silently removes every section, and the HTML still looks fine.
- **`setup()` registers directives and nothing else.** The single
  `config-inited` handler exists only because directive registration is
  last-one-wins.

See `src/extensions/score_module_verification_report/README.md` for the
configuration values and the full rationale.

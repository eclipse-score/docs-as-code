<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# `score_sphinx_needs_templates`

This extension contains the runtime support for the repository's Sphinx-Needs
`.need` templates. It is loaded by `score_sphinx_bundle` immediately after
`sphinx_needs`.

## Features

The extension provides:

* the shared `src/needs_templates` directory as the Sphinx-Needs template
  directory;
* the `linked_needs(need_id, link_name)` helper for traversing Need links;
* support for templates whose output depends on other Needs in the model.

## Using `linked_needs`

The helper returns the linked `NeedItem` objects in the order declared by the
source Need. This allows a template to derive its sections from the Need graph
instead of embedding Need IDs.

For example:

```jinja
{# score: render-after-needs-collection #}
{% set components = linked_needs(module_id, "includes") %}
{% for component in components %}
{{ component["title"] }}
{% endfor %}
```

Templates that follow links across the Need model should include the
`score: render-after-needs-collection` marker in a Jinja comment. Need fields and filters
continue to expose the corresponding backlink fields with the `_back` suffix.

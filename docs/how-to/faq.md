<!-- **************************************************************************
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-License-Identifier: Apache-2.0
*************************************************************************** -->

# FAQ

*docs-as-code is the S-CORE tool for building documentation, defining requirements and
verifying compliance.*

In this document you will find answers to frequently asked questions regarding
docs-as-code and its usage.


## Why is docs-as-code so slow?

The performance of docs-as-code has significantly improved in version 1.0.0 and later.

## IDE support (auto completion, metamodel checks, preview, LSP capabilities)

Since 1.0.0 IDE support works via esbonio. You'll need to install the esbonio extension
for your IDE (e.g., VSCode, PyCharm, etc.). Your repository must also be configured for
esbonio (settings.json).

If this does not work, please use the live preview feature: `bazel run //:live_preview`.
This provides immediate metamodel feedback (although only on the console) and
IDE-agnostic preview capabilities.


### Esbonio

Known issues:
* Python is required at startup, which is a problem for any Python-based LSP. We are
  working to improve this by providing a devcontainer with Python preinstalled.
  Additionally, we have submitted a feature request for Esbonio to handle Python
  installation.

  For now please run `bazel run //:ide_support` and restart VS Code.


### uBc

Currently, uBc is not aware of our metamodel. As a result, checks and auto-completion
features are not available.

We plan to explore improvements in this area in the future together with useblocks.



## Do we need to write custom Python code for every Metamodel check?
With our current approach, allowed attributes and links for Needs are defined within the
`metamodel.yml` file. If the check can be fully described there (e.g., process
requirements are only allowed to link to stakeholder requirements), no custom code is
needed. It is also not necessary to write individual tests for every single check
performed by the metamodel.

Only a few very specific checks require custom Python code beyond the generic metamodel
capabilities. These are cases that cannot be addressed by generic metamodel approaches
in any tool. For example: "the middle part of certain IDs must match the directory name
of the file."


## How can I be sure that the Metamodel does what I want it to do?
We use *examples* written in reStructuredText (rst) to verify that the metamodel has
been configured as intended.

Metamodel checks are verified through standard testing practices, like any other code.
The examples mentioned above are helpful, but they are only examples. They are not
mandatory for verification of the metamodel checks.



## Sphinx and safety
It is important to distinguish between metamodel checks and HTML rendering.

Metamodel checks can be verified / qualified without Sphinx.

If the renderer is safety-relevant, then qualification of Sphinx (and Sphinx Needs) is
required. This is currently under evaluation by the process team (@aschemmel-tech).


## What about versioning of requirements?
We are currently discussing possible implementations to enable linking to specific
versions of requirements (e.g. `implements: req-5@v3.0.0`).


## Sphinx traceability
It is possible to link requirements from other requirements, from source code, or from
tests (tests within the next days).

### What about bazel targets?
Bazel targets are not involved in traceability (currently not required by process).

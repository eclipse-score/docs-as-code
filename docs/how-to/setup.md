<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

(setup)=
# Setup


## Overview

docs-as-code allows you to easily integrate Sphinx documentation generation into your
Bazel build system. It provides a collection of utilities and extensions specifically
designed to enhance documentation capabilities in S-CORE.

## Features

- Seamless integration with Bazel build system
- S-CORE process compliance
- Support for PlantUML diagrams
- Source code linking capabilities
- S-CORE layouts and themes

## Installation

### 1. MODULE.bazel file

Add the module to your `MODULE.bazel` file:

```starlark
bazel_dep(name = "score_docs_as_code", version = "4.1.0")
```

And make sure to also add the S-core Bazel registry to your `.bazelrc` file

```starlark
common --registry=https://raw.githubusercontent.com/eclipse-score/bazel_registry/main/
common --registry=https://bcr.bazel.build
```

### 2. .bazelrc file

Since we use `PlantUML <https://www.plantuml.com>`_ for diagrams, we need some Java.
If there is no Java on your system, Bazel can download a remote JDK for you
but that requires some configuration in your `.bazelrc` file:

```
build --java_language_version=17
build --java_runtime_version=remotejdk_17
build --tool_java_language_version=17
build --tool_java_runtime_version=remotejdk_17
```

### 3. BUILD file


```starlark
load("@score_docs_as_code//:docs.bzl", "docs")

docs(
    source_dir = "<your sphinx source dir>",
    project = "<your project name>",
    project_url = "https://example.com/<your-project>",
    data = [
        "@other_repo:needs_json",  # Optional, if you have dependencies
    ],
)
```

For configuration options see {ref}`docs_bazel-macros`.

### 4. Optional: add conf.py

No `conf.py` is required for the default setup. The `docs()` macro generates
one from `project` and `project_url`; the Docs-as-Code version and baseline
extensions are supplied automatically.

Add a `conf.py` to your source directory only when you need additional Sphinx
configuration. When it exists, it remains the authoritative configuration.

Note that conf.py will affect only local builds. It will not affect the integrated
documentation build by reference_integration. Local builds are useful for testing and
debugging your documentation before committing changes. Not for final delivery. HAving a
custom conf.py is highly discouraged.

#### 5. Run a documentation build:


```bash
bazel run //:docs
```

#### 6. Access your documentation at

`/_build/index.html`

## Next Step

After basic setup, see {doc}`dashboards_and_quality_gates` to configure
traceability dashboards, export `metrics.json`, and enforce CI quality gates in
consumer repositories.

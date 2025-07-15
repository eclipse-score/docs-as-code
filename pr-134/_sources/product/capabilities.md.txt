(capabilities)=

# 📘 S-CORE Docs-as-Code – Capabilities

This document outlines the key capabilities of the S-CORE docs-as-code tooling.
Core capabilities of [Sphinx](https://www.sphinx-doc.org/) and [sphinx-needs](https://sphinx-needs.readthedocs.io/) are assumed and extended with S-CORE-specific conventions and infrastructure.

## Input Format

- Supports both reStructuredText (rst) and Markdown (CommonMark/GFM)

## Build

- Ensures deterministic output: identical input produces identical output
- ✅ Uses version-controlled configuration to ensure reproducibility
- ✅ Behaves consistently across different repositories and environments (e.g., local, CI/CD)
- ✅ Supports incremental builds to provide fast feedback during authoring
- ✅ Seamless integration with the Bazel build system

## Configuration

- ✅ Uses a single, shared, version-controlled configuration file
- ✅ Allows repository-specific overrides when needed
- ✅ Supports easy configuration of the metamodel (e.g., used roles, types)
- ✅ Ensures consistency with process and quality requirements



## Cross-Repository Linking

- ✅ Supports unidirectional links to:
  - Versioned documentation (for tagged releases)
  - Latest documentation (e.g. `main` branch)
- ✅ Keeps linked repositories and their rendered websites unaffected by incoming references
- Allows bidirectional links for integration-focused documentation
- In addition to high level versioning of repositories, supports verifying suspect links on a requirement level

## Previews & Feedback

- ✅ Automatically generates documentation previews for pull requests
- Previews are available within minutes of each push
- ✅ Preview output matches final published artifacts (identical rendering)

## IDE & Developer Experience

- ✅ Live preview functionality for documentation authors
- ✅ Integrated linting for:
  - Syntax and formatting (reST and Markdown)
  - Internal and external link validity
  - ✅ Metamodel compliance
- Auto-completion support for:
  - Cross-repository links
  - Sphinx directives and roles (planned)

## Architecture Visualization

- ✅ Generates architecture diagrams from structured models
- Integrates diagram tools such as PlantUML and Mermaid

## Code Integration

- ✅ Enables traceability between documentation and source code by linking from implementation to requirements


## ⚙️ Bazel Support
*Used as the core build system across S-CORE*

- ✅ Automatically validates changes to the S-CORE Bazel registry
- ✅ IDE support for editing Bazel `BUILD` and `.bzl` files (via LSP, plugins)

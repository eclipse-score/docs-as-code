<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Schema Export Package

This package provides tools to export the S-CORE metamodel as JSON Schema and instance data.

## Purpose

The schema export package enables AI agents and other tools to:
1. Understand the metamodel structure via JSON Schema
2. Validate metamodel instances
3. Consume metamodel data for downstream processing

## Tools

### 1. `generate_schema.py` - JSON Schema Generator

Generates a JSON Schema that describes the structure and validation rules of the S-CORE metamodel.

```bash
bazel run //src/extensions/score_metamodel/schema_export:generate_schema_bin -- \
  --output path/to/metamodel-schema.json
```

### 2. `export_data.py` - Metamodel Data Exporter

Exports the actual metamodel instance data from `metamodel.yaml` into JSON format.

The source commit is read from the `SOURCE_COMMIT` environment variable or can be
specified via the `--source-commit` argument.

```bash
# Using environment variable
export SOURCE_COMMIT=$(git rev-parse HEAD)
bazel run //src/extensions/score_metamodel/schema_export:export_data_bin -- \
  --output path/to/metamodel-data.json

# Or using argument
bazel run //src/extensions/score_metamodel/schema_export:export_data_bin -- \
  --output path/to/metamodel-data.json \
  --source-commit $(git rev-parse HEAD)
```

### 3. `generate_all.py` - Combined Generator

Generates both schema and data in one call, suitable for CI/CD pipelines.

The source commit is read from the `SOURCE_COMMIT` environment variable or can be
specified via the `--source-commit` argument.

```bash
# Using environment variable
export SOURCE_COMMIT=$(git rev-parse HEAD)
bazel run //src/extensions/score_metamodel/schema_export:generate_all_bin -- \
  --output-dir path/to/output

# Or using argument
bazel run //src/extensions/score_metamodel/schema_export:generate_all_bin -- \
  --output-dir path/to/output \
  --source-commit $(git rev-parse HEAD)
```

## Output Files

### `metamodel-schema.json`

A JSON Schema document that defines:
- Structure of need types and their options
- Link type definitions
- Prohibited words validation rules
- Graph validation rules
- Base options inherited by all types

### `metamodel-data.json`

An instance document containing:
- All need types with their configurations
- All link types
- Prohibited words checks
- Graph validation rules
- Source metadata (commit SHA, repo URL)

## Usage in CI/CD

The tools are designed to be run in CI/CD pipelines to generate schema and data files that can be:

1. **Published to a schema registry**: Make the schema available for validation
2. **Consumed by mcp-server**: The metamodel-flow package uses this data
3. **Used for validation**: AI agents can validate metamodel instances

### Example CI Pipeline

```yaml
# In your CI configuration
- name: Generate Metamodel Schema
  run: |
    bazel run //src/extensions/score_metamodel/schema_export:generate_all_bin -- \
      --output-dir bazel-out/metamodel \
      --source-commit ${{ github.sha }}

- name: Upload Schema Artifacts
  uses: actions/upload-artifact@v4
  with:
    name: metamodel-schema
    path: bazel-out/metamodel/
```

## Integration with mcp-server

The generated `metamodel-data.json` is consumed by the `metamodel-flow` package in the mcp-servers repository:

```
docs-as-code (metamodel.yaml)
    → JSON Schema + Data Export
    → mcp-servers (metamodel-data.json)
    → Process Description Model
```

## Development

### Running Tests

```bash
bazel test //src/extensions/score_metamodel/schema_export:unit_tests
```

### Local Development

```bash
# Using Python directly
python src/extensions/score_metamodel/schema_export/generate_all.py \
  --output-dir /tmp/metamodel_output \
  --source-commit $(git rev-parse HEAD)

# Check output
ls -lh /tmp/metamodel_output/
```

## Schema Version

The current schema version is `1`. Future versions will maintain backward compatibility where possible.

## License

Apache-2.0

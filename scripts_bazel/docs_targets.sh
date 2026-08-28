#!/usr/bin/env bash
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

query_scope="${1:-//...}"

docs_targets="$(bazel query \
  'attr(generator_function, "^docs$", '"${query_scope}"')' \
  --output=label)"
bundle_targets="$(bazel query \
  'kind("_docs_bundle rule", attr(generator_function, "^docs_bundle$", '"${query_scope}"'))' \
  --output=label)"
bundle_needs_targets="$(bazel query \
  'attr(generator_function, "^docs_bundle$", '"${query_scope}"')' \
  --output=label)"

query_output="$(
    {
        while IFS= read -r target; do
            [[ -n "$target" ]] || continue
            case "$target" in
                */tests/*|*.run|*.serve|*.venv|*.find_main)
                    continue
                    ;;
            esac
            name="${target##*:}"
            case "$name" in
                docs|docs_check|docs_link_check|live_preview|ide_support|\
                needs_json|needs_json_file|metrics_json|sourcelinks_json|traceability_gate)
                    printf 'docs\t%s\n' "$target"
                    ;;
            esac
        done <<< "$docs_targets"

        while IFS= read -r target; do
            [[ -n "$target" ]] || continue
            case "$target" in
                */tests/*|*.run|*.serve|*.venv|*.find_main)
                    continue
                    ;;
            esac
            name="${target##*:}"
            [[ "$name" != _* ]] && printf 'bundle\t%s\n' "$target"
        done <<< "$bundle_targets"

        while IFS= read -r target; do
            [[ -n "$target" ]] || continue
            case "$target" in
                */tests/*|*.run|*.serve|*.venv|*.find_main)
                    continue
                    ;;
            esac
            name="${target##*:}"
            case "$name" in
                _*_needs_local)
                    ;;
                _*_needs_upward)
                    ;;
                *_needs_local)
                    printf 'local\t%s\n' "$target"
                    ;;
                *_needs_upward)
                    printf 'upward\t%s\n' "$target"
                    ;;
            esac
        done <<< "$bundle_needs_targets"
    } | LC_ALL=C sort -t $'\t' -k2,2 -u
)"

while IFS=$'\t' read -r role target; do
    [[ -n "$target" ]] || continue

    name="${target##*:}"
    case "$role" in
        bundle)
            description="mountable and composable documentation bundle"
            ;;
        local)
            description="bundle-local Needs export (own sources only)"
            ;;
        upward)
            description="bundle Needs export (own sources plus upward dependencies)"
            ;;
        docs)
            case "$name" in
                docs)
                    description="build the rendered documentation"
                    ;;
                docs_check)
                    description="run the documentation validation checks"
                    ;;
                docs_link_check)
                    description="check links in the documentation"
                    ;;
                live_preview)
                    description="run the live documentation preview"
                    ;;
                ide_support)
                    description="create the documentation development virtualenv"
                    ;;
                needs_json)
                    description="build the complete composed Needs graph"
                    ;;
                needs_json_file)
                    description="export the complete composed Needs graph as JSON"
                    ;;
                metrics_json)
                    description="export traceability metrics from the Needs build"
                    ;;
                sourcelinks_json)
                    description="export merged source-to-documentation links"
                    ;;
                traceability_gate)
                    description="enforce configured traceability coverage thresholds"
                    ;;
            esac
            ;;
    esac

    printf '%-90s %s\n' "$target" "$description"
done <<< "$query_output"

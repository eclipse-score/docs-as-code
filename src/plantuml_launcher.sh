#!/usr/bin/env bash
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

if [[ -n "${RUNFILES_DIR:-}" ]]; then
  runfiles="$RUNFILES_DIR"
elif [[ -d "$0.runfiles" ]]; then
  runfiles="$0.runfiles"
elif [[ "$0" == *.runfiles/* ]]; then
  runfiles="${0%.runfiles/*}.runfiles"
else
  echo "Cannot locate PlantUML runfiles directory" >&2
  exit 1
fi

# Find the artifact selected by Bazel. The main-repository mapping contains
# only apparent-to-canonical external repo mappings; runfiles entries use the
# canonical name such as +_repo_rules+plantuml_native_linux_amd64.
for candidate in \
  +_repo_rules+plantuml_native_linux_amd64/plantuml \
  +_repo_rules+plantuml_native_linux_arm64/plantuml \
  +_repo_rules+plantuml_native_macos_arm64/plantuml \
  +_repo_rules+plantuml_native_windows_amd64/plantuml.exe; do
  path="$runfiles/$candidate"
  if [[ -x "$path" ]]; then
    exec "$path" "$@"
  fi
  if [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
    resolved="$(awk -v key="$candidate" 'index($0, key " ") == 1 { print substr($0, length(key) + 2); exit }' "$RUNFILES_MANIFEST_FILE")"
    if [[ -n "$resolved" && -x "$resolved" ]]; then
      exec "$resolved" "$@"
    fi
  fi
done

echo "Selected PlantUML binary was not found in runfiles" >&2
exit 1

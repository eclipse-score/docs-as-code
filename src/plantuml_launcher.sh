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

# Bazel may canonicalize repository names in runfiles. Translate the apparent
# repo name through the root mapping when available, then try the direct name.
mapping="${RUNFILES_MANIFEST_FILE:-$runfiles/MANIFEST}"
for repo in plantuml_native_linux_amd64 plantuml_native_linux_arm64 plantuml_native_macos_arm64 plantuml_native_windows_amd64; do
  canonical="$repo"
  if [[ -f "$runfiles/_repo_mapping" ]]; then
    mapped="$(awk -F, -v repo="$repo" '$1 == "" && $2 == repo { print $3; exit }' "$runfiles/_repo_mapping")"
    [[ -z "$mapped" ]] || canonical="$mapped"
  fi
  for candidate in "$canonical/plantuml" "$canonical/plantuml.exe" "$repo/plantuml" "$repo/plantuml.exe"; do
    path="$runfiles/$candidate"
    if [[ -f "$path" ]]; then
      exec "$path" "$@"
    fi
    if [[ -f "$mapping" ]]; then
      resolved="$(awk -v key="$candidate" 'index($0, key " ") == 1 { print substr($0, length(key) + 2); exit }' "$mapping")"
      if [[ -n "$resolved" && -f "$resolved" ]]; then
        exec "$resolved" "$@"
      fi
    fi
  done
done

echo "Selected PlantUML binary was not found in runfiles" >&2
exit 1

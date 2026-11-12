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

# Direct invocations do not necessarily inherit Bazel's runfiles environment.
# Manifest-only builds place the manifest beside the public executable.
if [[ -z "${RUNFILES_MANIFEST_FILE:-}" ]]; then
  if [[ -f "$0.runfiles_manifest" ]]; then
    export RUNFILES_MANIFEST_FILE="$0.runfiles_manifest"
  elif [[ -f "$0.runfiles/MANIFEST" ]]; then
    export RUNFILES_MANIFEST_FILE="$0.runfiles/MANIFEST"
  fi
fi

if [[ -n "${RUNFILES_DIR:-}" ]]; then
  runfiles="$RUNFILES_DIR"
elif [[ -d "$0.runfiles" ]]; then
  runfiles="$0.runfiles"
elif [[ "$0" == *.runfiles/* ]]; then
  runfiles="${0%.runfiles/*}.runfiles"
else
  runfiles=""
fi

runfiles_library="$runfiles/bazel_tools/tools/bash/runfiles/runfiles.bash"
if [[ ! -f "$runfiles_library" && -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
  runfiles_library="$(awk '$1 == "bazel_tools/tools/bash/runfiles/runfiles.bash" { print substr($0, index($0, " ") + 1); exit }' "$RUNFILES_MANIFEST_FILE")"
fi
if [[ ! -f "$runfiles_library" ]]; then
  echo "Cannot find Bazel runfiles library" >&2
  exit 1
fi
# rlocation reads the environment, including when the containing runfiles tree
# was discovered from this executable's path rather than supplied by the caller.
if [[ -n "$runfiles" ]]; then
  export RUNFILES_DIR="$runfiles"
fi
# shellcheck disable=SC1090
source "$runfiles_library"

# The build embeds the selected artifact's canonical runfiles key. rlocation
# handles both directory trees and manifest-only runfiles without changing args.
binary="$(rlocation '@@PLANTUML_RUNFILE@@')" || binary=""
if [[ ! -x "$binary" ]]; then
  echo "Selected PlantUML binary was not found in runfiles: @@PLANTUML_RUNFILE@@" >&2
  exit 1
fi
exec "$binary" "$@"

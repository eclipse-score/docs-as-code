<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# heldout-cr5-01

Input: listed before/after needs snapshots and before/after schema-v2 metrics.
Fixed context: native gate and catalog rules CR-005.
Success: verdict `fail`; impacted IDs `coverage`.
Gate options: `--min-req-code 75 --min-req-test 50 --fail-on-broken-test-refs`.
Metrics source: executable native-gate seed.
Source: scripts_bazel/tests/traceability_gate_test.py; public modeled argument snapshots. Public seed, not a historical field defect.
Split: heldout. Outcomes specified before candidate evaluation.

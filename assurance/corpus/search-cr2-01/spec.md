<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# search-cr2-01

Input: listed before/after needs snapshots and before/after schema-v2 metrics.
Fixed context: native gate and catalog rules CR-002.
Success: verdict `pass`; impacted IDs `A2_search_0, G2_search_0, R2_search_0, T2_search_0`.
Gate options: `--min-req-code 75 --min-req-test 50 --fail-on-broken-test-refs`.
Metrics source: executable native-gate seed.
Source: scripts_bazel/tests/traceability_gate_test.py; public modeled argument snapshots. Public seed, not a historical field defect.
Split: search. Outcomes specified before candidate evaluation.

Expected impact list includes every reachable node through requirement/test evidence cycles, as specified by the issue graph-propagation rule.

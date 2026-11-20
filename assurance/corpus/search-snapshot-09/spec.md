<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# search-snapshot-09

Input: listed before/after needs snapshots and before/after schema-v2 metrics.
Fixed context: native gate and catalog rules CR-005.
Success: verdict `fail`; impacted IDs `R0, R1, R2, T, coverage`.
Gate options: `--need-type tool_req --min-req-code 100`.
Metrics source: snapshot.
Source: src/extensions/score_metrics/traceability_metrics.py native extraction and scripts_bazel/tests/traceability_gate_test.py type-scoped threshold seeds. Public seed, not a historical field defect.
Split: search. Outcomes specified before candidate evaluation.

Expected impact list includes every reachable node through requirement/test evidence cycles, as specified by the issue graph-propagation rule.

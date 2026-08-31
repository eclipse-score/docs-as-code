<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Agent guidance

## Explain comments at the right level

Code comments document the code that exists now. When behavior is not
self-explanatory, explain what the code does and why that behavior is needed.
Do not describe the change relative to removed or previous code in inline
comments.

Explain the delta of a change in the pull request description instead: state
what changed, why it changed, and how the regression coverage demonstrates the
intended behavior.

Tests are documentation as well as verification. Make non-obvious assertions
self-explanatory through a descriptive test name, a concise docstring, or
nearby context that identifies the relevant setup, expected result, and reason.

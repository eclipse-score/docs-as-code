<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# Decision Record: Why extensions?

Instead of setting global variables in conf.py which may be incorrect,
misspelled, have the wrong type etc., we can use extensions to setup sphinx,
sphinx-needs and other extensions.
This way we interact through a typesafe API and can be sure that the
configuration is correct.

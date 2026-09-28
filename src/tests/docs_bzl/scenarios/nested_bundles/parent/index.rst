..
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

Parent bundle
=============

.. tool_req:: A nested bundle can be mounted into a documentation tree
   :id: tool_req__docs_bzl_nested_bundle
   :version: 1
   :satisfies: gd_req__docs_bzl_nested_bundle

   The ``parent`` bundle composes the ``child`` bundle and can be mounted into
   a host documentation tree together with its generated data.

.. gd_req:: Nested bundles compose generated data through mount points
   :id: gd_req__docs_bzl_nested_bundle
   :version: 1

   When a nested bundle is mounted into a host documentation tree, the
   generated data of its child bundle must be composed with the parent bundle.

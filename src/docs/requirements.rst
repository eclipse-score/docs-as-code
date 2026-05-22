..
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   SPDX-License-Identifier: Apache-2.0

Requirements
============

.. stkh_req:: Mount external source trees for IDE consumption
   :id: stkh_req__docs__mounts
   :reqtype: Functional
   :safety: QM
   :security: NO
   :status: valid
   :rationale: Out-of-tree documentation must reach the rendered site without copying, and IDE tooling must read the same project configuration Sphinx reads so editing inside a mounted bundle gets as-you-type validation without invoking Sphinx.

   As a stakeholder of S-CORE docs-as-code, I want the ``docs()``
   Bazel macro to expose mounted external source bundles via a
   declarative ``[[mounts]]`` block in the generated
   ``ubproject.toml``, so that IDE extensions can resolve documents
   inside those bundles without invoking Sphinx.

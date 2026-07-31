..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

Cross-Module Compatibility Findings
===================================

When documentation bundles from independently released Bazel modules are
mounted together, the complete build uses one Sphinx-Needs and metamodel
baseline.  A supplier can therefore be valid on its own release baseline while
an integrated build detects a newer requirement.

Docs-as-code keeps standalone builds strict.  Cross-module compatibility is
also strict by default: no finding is downgraded unless its category is enabled
explicitly in ``conf.py``:

.. code-block:: python

   score_cross_module_compatibility_allow_missing_mandatory_attributes = True
   score_cross_module_compatibility_allow_missing_mandatory_links = True
   score_cross_module_compatibility_allow_version_mismatches = True

Each switch applies only to needs owned by mounted or imported modules.  Local
findings remain fatal.  The switches enable these non-fatal findings:

* missing mandatory attributes;
* missing mandatory links; and
* an exact need-link version condition such as ``target[version==1]`` that does
  not match when at least one link endpoint is external.

All other metamodel findings, all-local links, and every malformed or failed
Sphinx-Needs link condition remain fatal.

Reports
-------

The HTML landing page displays a warning when findings exist.  Every successful
HTML build also writes these files into its output directory:

``compatibility-findings.json``
  Machine-readable summary and findings for CI.  A finding contains the owning
  module, source need, optional target need, category and message.

``compatibility-findings.html``
  Human-readable detailed report grouped by supplying module.

Treat findings as upgrade work: they make integration possible during a version
skew, but they do not make the underlying mismatch disappear.

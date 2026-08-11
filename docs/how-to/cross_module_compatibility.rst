..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

Handle Cross-Module Compatibility Findings
==========================================

Use this guide when mounting documentation from another module causes a
metamodel or Sphinx-Needs validation failure. The goal is to keep the
integration build working while making the incompatibility visible and tracking
the supplier upgrade needed to remove it.

1. Identify the failing compatibility category
----------------------------------------------

Build the documentation as usual:

.. code-block:: bash

   bazel run //:docs

By default, all validation findings fail the build. Check the build output to
identify whether the mounted module has a missing mandatory attribute, a
missing mandatory link, or an exact version condition that no longer matches.

2. Allow only the affected category
-----------------------------------

Add the corresponding temporary setting to the consumer's ``docs/conf.py``:

.. code-block:: python

   # Use only the setting that matches the finding.
   score_cross_module_compatibility_allow_missing_mandatory_attributes = True
   score_cross_module_compatibility_allow_missing_mandatory_links = True
   score_cross_module_compatibility_allow_version_mismatches = True

Choose the setting that matches the failure:

* ``score_cross_module_compatibility_allow_missing_mandatory_attributes`` for
  a required attribute missing in an external module;
* ``score_cross_module_compatibility_allow_missing_mandatory_links`` for a
  required link missing in an external module; or
* ``score_cross_module_compatibility_allow_version_mismatches`` for an exact
  link condition such as ``target[version==1]`` that does not match an external
  endpoint.

Do not enable a category merely to suppress an unrelated local validation
failure: local findings remain fatal.

3. Review the generated findings
--------------------------------

Build again. The HTML landing page warns when compatibility findings exist, and
the HTML output directory contains:

``compatibility-findings.json``
  Use this machine-readable report in CI or issue tracking. Each finding
  identifies the owning module, source need, optional target need, category,
  and message.

``compatibility-findings.html``
  Open this report to review findings grouped by supplying module.

4. Remove the temporary allowance
---------------------------------

Update or coordinate with the supplying module so that it meets the integrated
baseline. Then remove the corresponding setting from ``conf.py`` and rebuild.
The build must pass with the default strict validation before the compatibility
work is complete.

For the policy behind these settings and their exact scope, see
:doc:`../concepts/cross_module_compatibility`.

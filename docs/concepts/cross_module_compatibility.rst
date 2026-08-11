..
   # *******************************************************************************
   # Copyright (c) 2026 Contributors to the Eclipse Foundation
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************

Cross-Module Compatibility
==========================

When documentation bundles from independently released Bazel modules are
mounted together, the complete build uses one Sphinx-Needs and metamodel
baseline. A supplier can therefore be valid on its own release baseline while
an integrated build detects a newer requirement.

Docs-as-code keeps standalone builds strict. Cross-module compatibility is also
strict by default: no finding is downgraded unless its category is enabled
explicitly in ``conf.py``.

Scope of Compatibility Allowances
---------------------------------

Each allowance applies only to needs owned by mounted or imported modules. It
can downgrade these findings:

* missing mandatory attributes;
* missing mandatory links; and
* an exact need-link version condition such as ``target[version==1]`` that does
  not match when at least one link endpoint is external.

All other metamodel findings, all-local links, and every malformed or failed
Sphinx-Needs link condition remain fatal. An allowance makes an integration
possible during version skew; it does not make the underlying mismatch valid.

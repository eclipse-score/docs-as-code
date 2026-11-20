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
* missing mandatory links declared on a need type;
* absent relations required by metamodel graph rules on mounted needs; and
* an exact need-link version condition such as ``target[version==1]`` that does
  not match when at least one link endpoint is external.

For a graph rule, the allowance applies to an empty relation checked by
``check_one``, including a backlink. A declared link with an unresolved target
or a target that fails the graph predicate still fails validation. The report
includes the graph rule ID and relation.

All other metamodel findings and all-local links keep their usual validation
behavior. An allowance makes an integration possible during version skew; it
does not make the underlying mismatch valid.

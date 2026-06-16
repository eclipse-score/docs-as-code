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

Write Documentation
===================

Outside Documentation
^^^^^^^^^^^^^^^^^^^^^

`Sphinx <https://www.sphinx-doc.org/en/master/>`_:
the documentation generator we use.

`reStructuredText (reST) <https://docutils.sourceforge.io/rst.html>`_:
the plain-text markup language used for most source files in this project.

`Sphinx-Needs <https://sphinx-needs.readthedocs.io/en/latest/>`_:
a Sphinx extension that models requirements, tests, tasks and other "needs" inside the docs.


Advanced
^^^^^^^^

Needextend
~~~~~~~~~~

Needextend allows you to extend needs that are defined in the documentation.
The scope of allowed behaviour in Docs-As-Code for needextend is limited as we do not allow all of its usecases.

Allowed usecases:

* Setting an attribute or Link **IF** it is not already set in the need that is getting modified
* Appending to a list of links

Not Allowed:

* Overwriting an attribute or Link that already is set in the need that gets modified
* Deleting an attribute or Link

.. code-block:: rst

      .. stkh_req:: Test Req Extends 1
         :id: stkh_req__test__need_extends_1
         :status: invalid


      # ✅ ALLOWED => The replacing of attributes on needs that are NOT set.
      .. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
         :safety: NO


      # ❌ NOT ALLOWED => Overwriting attributes that are already set in the need
      .. needextend:: c.this_doc() and id == 'stkh_req__test__need_extends_1'
         :status: valid


For further documentation on needextends please `look here <https://sphinx-needs.readthedocs.io/en/latest/directives/needextend.html>`_

.. note::

   In the future we will enable a check that needextends will only modify needs in the current document.
   You can ensure this by adding `c.this_doc()` to the filter string of the need.


Requirement ID Feature Part
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requirement IDs with 3 parts (defined by the Metamodel) follow the format ``<Type>__<feature>__<Title>``.
The ``<feature>`` part must relate to where the requirement lives in the documentation,
so that IDs stay meaningful and traceable as the project evolves.

The feature part is validated by checking that at least one of the following is true:

* A segment of the feature part (split on ``_`` and ``-``) appears in the document's directory path
* The initials of the feature part's segments appear in the document's directory path
* The feature part contains a string explicitly allowed via ``required_in_id`` in ``conf.py``

**Examples** — given a requirement in ``internals/safety/fmea/requirements.rst``:

.. list-table::
   :header-rows: 1
   :widths: 45 10 45

   * - ID
     -
     - Reason
   * - ``feat_saf__fmea__late_message``
     - ✅
     - ``fmea`` is in the path
   * - ``feat_saf__safety_fmea__late_message``
     - ✅
     - ``safety`` and ``fmea`` are in the path
   * - ``feat_saf__sf__late_message``
     - ✅
     - ``sf`` are the initials of ``safety_fmea``, which is in the path
   * - ``feat_saf__blabla__late_message``
     - ❌
     - ``blabla`` has no relation to the path ``internals/safety/fmea``

To explicitly allow a feature part that intentionally doesn't match the path
(e.g. in a single module repository), add a matching string to ``required_in_id`` in ``conf.py``:

.. code-block:: python

   # conf.py
   required_in_id = ["persistenc"]

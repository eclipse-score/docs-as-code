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

.. _docs_dependencies:

==========================
Docs Dependencies
==========================

When running ``bazel run :docs``, the documentation build system orchestrates multiple interconnected dependencies to produce HTML documentation.

1. Gather inputs (Bazel may do this parallelized):

   * Extract source code links from files via ``sourcelinks_json`` rule.

     * Optionally, merge source links using the ``merge_sourcelinks`` rule.

   * Imported Needs are gathered from public ``docs()`` or ``docs_bundle``
     targets specified in ``external_needs``. The ``needs_json`` label remains
     accepted as a deprecated form without a warning for now; ``needs_json_file``
     remains supported for directly naming an inventory file. Passing a Needs
     inventory through ``data`` is deprecated and prints an informational
     message; declare it through ``external_needs`` instead.

2. Documentation sources are read from the specified source directory (default: ``docs/``).
   Sphinx processes the documentation sources along with the merged data to generate the final HTML output.

.. plantuml::

	 @startuml
    left to right direction

	 collections "Documentation Sources" as DocsSource
	 collections "Needs JSON Targets" as NeedsTargets
	 collections "Source Code Links" as SourceLinks
	 artifact "Merge Data" as Merge
	 process "Sphinx Processing" as Sphinx
	 artifact "HTML Output" as HTMLOutput
    collections "S-CORE extensions" as SCoreExt

	 DocsSource --> Sphinx
	 NeedsTargets --> Sphinx
    SCoreExt --> Sphinx
	 SourceLinks --> Merge
	 Merge --> Sphinx
	 Sphinx --> HTMLOutput

	 @enduml

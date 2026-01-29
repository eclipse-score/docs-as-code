
.. _docs_dependencies:

==========================
Docs Dependencies
==========================

When running ``bazel run :docs``, the documentation build system orchestrates multiple interconnected dependencies to produce HTML documentation.

1. Gather inputs (Bazel may do this parallelized):

   * Extract source code links from files via ``sourcelinks_json`` rule.

     * Optionally, merge source links using the ``merge_sourcelinks`` rule.

   * Needs (requirements) are gathered from various ``needs_json`` targets specified in the ``data`` attribute.

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

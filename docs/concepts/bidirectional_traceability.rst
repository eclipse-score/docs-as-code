.. _bidirectional_traceability:

Bi-directional Traceability
===========================

The S-CORE project uses a multi-repository layout for source and documentation.
To satisfy standards such as ASPICE and to support engineers and reviewers, documentation must provide reliable bi-directional traceability between needs, requirements, design artifacts and code.

Traceability in docs means two things in practice, e.g. if one requirement satisfies another one:

- forward links: from satisfier to satisfied need/requirement.
- backward links: satisfied requirement references all requirements it is satisfied by.

We support two complimentary strategies for providing these links in the published documentation:
build-with-links (fast build but only forward links) and
build-with-copies (self-contained release docs with backward links).
The Bazel-based doc build exposes both approaches via dedicated targets.

Strategies: links vs copies
---------------------------

Build with links
~~~~~~~~~~~~~~~~

.. code-block:: sh

   bazel run //:docs

The documentation build depends on the needs.json files from other modules.
The built site contains hyperlinks that point at the other repositories' documentation at https://eclipse-score.github.io.
For individual modules this means the build is relatively fast and this can be done in every pull request.

The tradeoff is that the target of the hyperlink is unaware.
That other module's need elements will not have backlinks.
At least not immediately.
In a later revision they can update their dependency on the first module and then the references are updated in their documentation.

Build with copies
~~~~~~~~~~~~~~~~~

.. code-block:: sh

   bazel run //:docs_combo_experimental

The documentation build does not depend on the needs.json but on whole documentation source code.

Using `sphinx_collections <https://sphinx-collections.readthedocs.io/en/latest/>`_
not just the current module is built but all referenced modules are included.

The advantage is that the produced documentation is consistent and stays that way.
There is no outwards hyperlink which could break or be outdated.

The tradeoff is that build takes longer and the output needs more space.
At the very least for release builds this is acceptable.


Module links vs Bazel target deps
---------------------------------

Remember: Bazel target dependencies must not be circular.
Module and document references may be circular.
Use the combo build and the copy strategy to produce release documentation that contains all needed pages while keeping Bazel's graph acyclic.



.. plantuml::

	 @startuml
	 ' Overall component style
	 skinparam componentStyle rectangle

	 ' Module-level (conceptual links can be circular)
	 	 component "<<module>> @A" as MA
	 	 component "<<module>> @B" as MB
	 	 ' Style bazel_dep edges: strong red, solid
	 	 MA =[#DarkRed]=> MB : bazel_dep
	 	 MB =[#DarkRed]=> MA : bazel_dep

	 ' Build-level (Bazel targets must be acyclic)
	 	 usecase "<<target>> @A:needs_json" as AT
	 	 usecase "<<target>> @B:needs_json" as BT
	 	 ' Style depends edge: blue dashed
	 	 AT .[#DodgerBlue].> BT : depends
	 	 ' Note: no BT --> AT allowed

	 ' Modules provide the targets used by the build
	 	 MA -[#ForestGreen]-> AT : provides
	 	 MB -[#ForestGreen]-> BT : provides

	 note left of MA
	 	 Module-level
	 	 references may be
	 	 bi-directional
	 end note

	 note right of BT
	 	 Bazel target deps
	 	 must be acyclic
	 end note

	 @enduml

The diagram above shows the difference between module-level references (which may be circular) and Bazel target dependencies (which must remain acyclic).
Module A and Module B may reference each other in documentation or design (bi-directional links).
Their corresponding Bazel targets must be arranged so the build dependency graph has no cycles.

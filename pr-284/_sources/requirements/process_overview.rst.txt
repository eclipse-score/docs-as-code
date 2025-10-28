.. _process_overview:

===============================
Process Requirements Overview
===============================

Unsatisfied Tool Requirements in Process
########################################

The following table lists tool requirements from our process which are not satisfied.

.. needtable::
   :types: gd_req
   :columns: id;title;satisfied by
   :colwidths: 2;4;1
   :style: table
   :filter_warning: No unsatisfied requirements, no table. ☺️

   results = []
   for need in needs.filter_types(["gd_req"]):
       if not need["id"].startswith("PROCESS_gd_req__tool_"):
          continue
       if len(need["satisfies_back"]) >= 1:
          continue
       results.append(need)

All our Tool Requirements
#########################

.. needtable::
   :types: tool_req
   :columns: satisfies as "Process Requirement" ;id as "Tool Requirement";implemented;source_code_link
   :style: table

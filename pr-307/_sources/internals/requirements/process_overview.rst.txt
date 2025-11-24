.. _process_overview:

===============================
Process Requirements Overview
===============================

Unsatisfied Process Requirements
################################

The following table lists tool requirements from our process
which are not (yet) satisfied,
i.e. covered by tool requirements.

.. needtable::
   :types: gd_req
   :columns: id;title;tags
   :colwidths: 2;4;2
   :style: table

   results = []
   prio = "prio_1"
   for need in needs.filter_types(["gd_req"]):
       if not any(prio in tag for tag in need["tags"]):
          continue
       if len(need["satisfies_back"]) >= 1:
          continue
       results.append(need)

.. needtable::
   :types: gd_req
   :columns: id;title;tags
   :colwidths: 2;4;2
   :style: table

   results = []
   prio = "prio_2"
   for need in needs.filter_types(["gd_req"]):
       if not any(prio in tag for tag in need["tags"]):
          continue
       if len(need["satisfies_back"]) >= 1:
          continue
       results.append(need)

.. TODO: add prio_3 once prio_1 is done

Requirements not fully implemented
##################################

Just because a process requirement is covered by tool requirements
does not mean it is implemented.

.. needtable::
   :types: gd_req
   :columns: id as "Process Requirement";implemented;satisfies
   :colwidths: 1;1;2
   :style: table

   results = []
   for need in needs.filter_types(["tool_req"]):
      if need["implemented"] == "YES":
         continue
      results.append(need)

All our Tool Requirements
#########################

.. needtable::
   :types: tool_req
   :columns: satisfies as "Process Requirement" ;id as "Tool Requirement";implemented;source_code_link
   :style: table

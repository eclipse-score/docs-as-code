.. _process_overview:

===============================
Process Requirements Overview
===============================

.. needtable::
   :columns: satisfies_back as "Tool Requirement"; id as "Process Requirement";tags
   :style: table

   r = {}

   all = {}
   for need in needs:
      all[need['id']] = need

   for need in needs:
     if any(tag in need['tags'] for tag in ["done_automation", "prio_1_automation", "prio_2_automation", "prio_3_automation"]):
       if not "change_management" in need['tags']:
         # Filter out change management related requirements
         r[need['id']] = need

   for tool_req in needs.filter_types(['tool_req']):
     for process_req_id in tool_req['satisfies']:
        r[process_req_id] = all[process_req_id]

   results = r.values()

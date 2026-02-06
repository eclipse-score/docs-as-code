.. _process_overview:

===============================
Process Requirements Overview
===============================

This page shall provide an overview
how well this tool implements process requirements.

Unsatisfied Process Requirements
################################

The following table lists process requirements from our process
which are not (yet) satisfied,
i.e. covered by tool requirements.

Unsatisfied – Priority 1
------------------------

.. needtable::
   :types: gd_req
   :columns: id;title;tags
   :colwidths: 2;4;2
   :style: table

   results = []
   ignored_ids = [
      # Impact Analysis is free form text, thus not in scope of docs-as-code
      "gd_req__change_attr_impact_description",
      # Problem Reports are Github issues not docs-as-code
      "gd_req__problem_attr_anaylsis_results",
      "gd_req__problem_attr_classification",
      "gd_req__problem_attr_impact_description",
      "gd_req__problem_attr_milestone",
      "gd_req__problem_attr_safety_affected",
      "gd_req__problem_attr_security_affected",
      "gd_req__problem_attr_stakeholder",
      "gd_req__problem_attr_status",
      "gd_req__problem_attr_title",
      "gd_req__problem_check_closing",
      # Requirements for test frameworks are not in scope of docs-as-code
      "gd_req__verification_link_tests",
      "gd_req__verification_link_tests_cpp",
      "gd_req__verification_link_tests_python",
      "gd_req__verification_link_tests_rust",
   ]
   prio = "prio_1"
   for need in needs.filter_types(["gd_req"]):
       if need["id"] in ignored_ids:
          continue
       if not any(prio in tag for tag in need["tags"]):
          continue
       if len(need["satisfies_back"]) >= 1:
          continue
       results.append(need)

Unsatisfied – Priority 2
------------------------

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
   :columns: id as "Tool Requirement";implemented;satisfies
   :colwidths: 1;1;2
   :style: table

   results = []
   for need in needs.filter_types(["tool_req"]):
      if need["implemented"] == "YES":
         continue
      results.append(need)

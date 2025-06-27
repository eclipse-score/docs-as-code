gd_req__saf__attr_uid:
- Indicate the type of safety analysis -> feat/comp??
- Have a keyword describing the level of analysis -> fmea/dea. This should be first?!
- Have a keyword describing the content of analysis -> What are the allowed keywords? Is it just free text as in requirements?

gd_req__saf_attr_mitigation:
- What is a 'violation' ?

gd_req__saf__attr_mandatory:
- 'verfiies' in the template but not mentioned here. Is it mandatory? Option


gd_req__saf__linkage_fulfill, gd_req__saf__linkage_check, gd_req__saf__linkage_safety:
Not marked as mandatory, is it?

gd_req__saf__linkage:
Inverse direction

gd_req__saf_attr_mitigation:
Can not check if mitigation is requirement or text or none. Can only check if it's text or none?
In the template 'free text' is forbidden, but in process it's allowed.
We can only have free text or a needs-link in the attribute, not a mix.
When we use "mitigation" as a link to requirements, then there is no explicit "None" value. Maybe a dummy "not yet implemented requirement"?
gd_req__saf__attr_requirements_check says it is mandatory.

gd_req__saf_attr_mitigation_issue:
- Mandatory or not? Link to github issue?

gd_req__saf__attr_requirements_check:
Is it mandatory for all of them?
Which requirements can it link to?
Process says 'None' or 'Free text' is also allowed,but this goes against this then.

gd_req__saf__attr_hash:
Requirement unclear. Versioning of safety analysis happens by versioning the module where they are written. E.g. we have a process-release v1.0.2. That would include everything that is documented within process.

gd_req__saf__linkage_fulfill:
What is a parent architecture? What do we call that link?

gd_req__saf__attr_argument:
The argument becomes the need content, correct? So instead of "argument" we have "content". For FMEA + DFA!

gd_req__saf__attr_vid:
violation_id must be one from https://eclipse-score.github.io/process_description/main/process_areas/safety_analysis/guidance/dfa_failure_initiators.html? For example SC_01_05 is ok. SC_01_06 would be an error.

gd_guidl__fault_models:
same as before? It's the ID from Table 36? See https://eclipse-score.github.io/process_description/main/process_areas/safety_analysis/guidance/fault_models_guideline.html#gd_guidl__fault_models


PROCESS_gd_req__saf__attr_veffect:
v->f?

gd_req__saf__attr_requirements:
This is the bidirectional link of gd_req__saf_attr_mitigation?

gd_req__saf__attr_aou:
What attribute? Missing in templates.


----

Quite a lot of mismatches with gd_req__saf_ vs gd_req__saf__ (two underscores)

Safety Analys Template => Should it be named FMEA Template?!

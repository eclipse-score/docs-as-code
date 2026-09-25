<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# How to Apply the SCORE Tool Management Process

This guide explains how to execute the
[Eclipse SCORE Tool Management Process](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/tool_management_workflow.html)
using SCORE Docs-as-Code.

The goal is **not** to reproduce ISO 26262 or define a separate qualification
process. SCORE already defines the process. This guide explains how to represent
and execute that process with the available S-CORE Docs-as-Code model.

```{note}
This guide focuses on the safety-related evaluation and qualification aspects
of SCORE Tool Management. Security evaluation is outside this guide. Use the
[SCORE Security Analysis Guideline](https://eclipse-score.github.io/process_description/main/process_areas/security_analysis/guidance/security_analysis_guideline.html)
and applicable work products to identify relevant assets, threats, and impacts.
For example, data integrity may matter for a tool use case while data
availability does not; reflect that result in the TVR.
```

---

## Mental model

The important distinction is between:

- **Tool Verification Report (TVR, `doc_tool`)** — records the SCORE
  tool-management state and the overall evaluation result.
- **Tool requirements (`tool_req`)** — capabilities or behaviours provided by
  the tool, independent of whether a particular project use case uses them.
- **Tool use cases (`tool_usecase`)** — the usage context in which the project
  relies on the tool.
- **Potential tool malfunctions (`potential_tool_malfunction`)** — ways in which
  the expected tool behaviour can fail.
- **Safety measures** — measures active during intended tool usage that prevent
  or detect a potential malfunction.
- **Testcases (`testcase`)** — verification evidence for requirements. For tool
  qualification, these verify the relevant `tool_req` needs.

```{mermaid}
flowchart LR
    UC["tool_usecase<br/>Tool Use Case"]
    PM["potential_tool_malfunction<br/>Potential Tool Malfunction"]

    UP["upstream requirements<br/>(stkh_req, gd_req, feat_req, comp_req)"]
    TR["tool_req<br/>Tool Requirement"]
    TC["testcase<br/>Qualification Evidence"]

    PM -->|"nested under<br/>(parent_needs)"| UC
    PM -->|"violates"| TR

    TR -->|"satisfies<br/>(optional)"| UP
    TC -->|"fully_verifies /<br/>partially_verifies"| TR

    style UC fill:#E1D5E7
    style PM fill:#F8CECC
    style UP fill:#DAE8FC
    style TR fill:#F5F5F5
```

Two analysis perspectives answer different questions:

| Perspective | Question |
|---|---|
| **Evaluation / classification** | How can our intended use of the tool fail, and would the intended usage detect or prevent that failure? |
| **Qualification** | Do we have sufficient evidence that the specific tool version satisfies the tool requirements we rely on? |

Qualification evidence and detection sufficiency are separate decisions; see
[Qualification is not a detection measure](#qualification-is-not-a-detection-measure).

---

## External vs. self-developed tools

The evaluation is based on **how the project uses the tool**, not on who
developed it.

Use cases, potential malfunctions, safety impact, and detection are therefore
evaluated the same way for external and self-developed tools.

The differences matter mainly when defining requirements and qualification
evidence.

| Topic | External tool | Self-developed tool |
|---|---|---|
| Version | Pin the exact external version and relevant configuration | Identify the exact internal release/version |
| `tool_req` | Select the tool capabilities relevant to the evaluated use cases | Reuse existing tool requirements where suitable |
| Implementation | Usually treated largely as a black box | Architecture and implementation may be available |
| Existing tests | Vendor/upstream tests can be supporting information | Existing development tests may already provide qualification evidence |
| Qualification | Usually validate our `tool_req` against the configured external tool | Reuse suitable requirements-based tests where possible |
| Corrective action | Upgrade, configure, constrain usage, add detection, or replace | The tool implementation itself can also be changed |

Do not duplicate requirements or tests solely because a self-developed tool is
now managed through the SCORE Tool Management process.

---

## SCORE workflow at a glance

```{mermaid}
flowchart LR
    A["Create Tool Verification Report"] --> B["status = draft"]
    B --> C["Evaluate Tool"]
    C --> D["status = evaluated"]
    D --> E{"Qualification required?"}

    E -->|"No"| H["Review / approve TVR"]
    E -->|"Yes"| F["Qualify Tool"]
    F --> G["status = qualified"]
    G --> H

    H --> I["status = released"]

    H -. unsuccessful .-> J["status = rejected"]
```

The remainder of this guide follows these steps.

---

## Step 1 — Create the Tool Verification Report

### What to model

The SCORE Tool Verification Report (TVR) is represented by `doc_tool`.

The TVR uses the following relevant attributes:

- `status`: `draft | evaluated | qualified | released | rejected`
- `security_affected`: `YES | NO`
- `tool_version`: optional

The generated TVR report additionally shows:

- `safety_affected`, derived from the owned malfunctions
- SCORE Tool Confidence Level (SCORE TCL), derived from the owned malfunctions

The report author does not provide these summary values.

Record the tool's scope and purpose, relevant configuration, environment, constraints,
inputs, outputs, and available documentation when creating the TVR. Inputs and outputs
define the usage boundary and are needed to identify potential malfunctions.

The introduction should make the purpose and intended use visible before the
detailed evaluation. Model each intended use as a `tool_usecase`; the generated
report places an overview of those use cases before the evaluation result.

```{mermaid}
flowchart LR
    P["Tool purpose and scope"] --> U["Intended use cases<br/>(tool_usecase)"]
    U --> M["Potential malfunctions"]
    M --> Q["Qualification of relevant<br/>(tool_req) capabilities"]
```

Example structure:

````markdown
```{doc_tool} S-CORE Docs-as-Code Tool Verification Report
:id: doc_tool__s_core_docs_as_code
:status: draft
:security_affected: NO
:tool_version: <exact version>

Describe the tool, its purpose and intended use, relevant configuration,
environment, constraints, inputs, outputs, and available documentation.
```
````

```{note}
The report author provides the tool identity, status, and security relevance.
The safety summary and SCORE TCL are derived from the owned malfunction graph.
```

### External tool

Identify the exact version and configuration that is actually used.

Evaluate the exact tool instance used by the project, including its version,
plugins, configuration, and usage restrictions.

### Self-developed tool

Reference the project's normal version, release, or source-revision
identification. For example, a Git commit can identify the evaluated tool when
the relevant source and build context are clear. The TVR must make clear which
specific tool version or revision the evaluation applies to.

```{note}
The current SCORE tool-management model assumes one active TVR per tool. It
does not currently support maintaining multiple parallel TVRs for different
versions of the same tool, nor does it scope qualification testcases to a
particular TVR/version. This limitation must be addressed before that usage
pattern is introduced.
```

---

## Step 2 — Define how the project uses the tool

SCORE evaluates the tool in the context of its **use cases**.

A `tool_usecase` captures:

> **What are we relying on this tool to do in our development process?**

Represent a `tool_usecase` with the following relationships:

```yaml
tool_usecase:
  mandatory_links:
    belongs_to: doc_tool
```

The normal relationship is therefore:

```{mermaid}
flowchart LR
    UP["upstream requirements<br/>(stkh_req, gd_req, comp_req, feat_req)"]
    DT["doc_tool"]
    UC["tool_usecase"]
    TR["tool_req"]

    UC -->|"belongs_to<br/>(mandatory)"| DT
    TR -->|"satisfies<br/>(optional)"| UP

    style UP fill:#DAE8FC
    style UC fill:#E1D5E7
    style TR fill:#F5F5F5
```

Tool requirements may satisfy upstream requirements, including `stkh_req`,
`gd_req`, `feat_req`, and `comp_req`. The relevant upstream requirements should
be linked through `tool_req.satisfies` when relating a tool capability to an
upstream need.

### How to model `tool_usecase`

In the structured verification workflow, an `evaluated`, `qualified`, or
`released` TVR owns one or more `tool_usecase` records. A use case records the
context in which the project relies on the tool. The use case itself has no
direct requirement links; the relevant `tool_req` needs are associated through
the nested malfunctions, and upstream requirements are linked from those
`tool_req` needs. Existing TVRs without structured use cases remain accepted
for compatibility, but the workflow checker does not derive summary values for
them.

For example:

- upstream requirement (e.g. `stkh_req`, `gd_req`, `feat_req`, `comp_req`): the
  system-development process must provide valid requirements traceability,
- tool use case: validate requirement traceability during documentation builds,
- tool requirement: unresolved requirement links must be reported.

If an existing requirement already expresses the usage context exactly, avoid
inventing additional behaviour in the use case. Keep it as a thin
grouping/context element. The relevant `tool_req` needs remain linked through
the nested malfunctions.

```{important}
Write each `potential_tool_malfunction` nested inside its `tool_usecase`. The
nested structure creates the `parent_needs` relationship automatically; do not
add a separate `parent_needs` option. Therefore, once you model malfunctions,
place them under a `tool_usecase` even if that use case merely provides context
for an already well-scoped requirement.
```

### Tool model example

````markdown
```{tool_usecase} Validate requirement traceability during documentation builds
:id: tool_usecase__docs_as_code__traceability
:belongs_to: doc_tool__s_core_docs_as_code

The project relies on the documentation tooling to identify invalid or
unresolved requirement links before documentation is accepted.
```
````

A good use case describes project usage, not an implementation detail.

**Avoid:**

```text
Call Python function resolve_links().
```

**Prefer:**

```text
Validate requirement links during the documentation build.
```

### External tool

Define the `tool_req` needs from the tool capability being evaluated, not by
importing the vendor's complete specification.

Example:

```text
Tool use case:
Validate requirement traceability during documentation builds.

Tool requirement:
The tool shall report unresolved requirement links.
```

### Self-developed tool

Prefer reusing existing `tool_req` needs in the nested malfunctions.

Do not create separate "qualification requirements" when the normal tool
requirements already describe the capability relevant to the project use case.

---

## Step 3 — Identify potential tool malfunctions

For every tool use case, identify relevant ways in which the expected tool
behaviour could fail.

Represent a `potential_tool_malfunction` with the following options and links:

```yaml
potential_tool_malfunction:
  mandatory_options:
    safety_affected: "^(YES|NO)$"
  optional_options:
    detection_sufficient: "^(YES|NO)$"
    safety_measures: ^.+$
  mandatory_links:
    # Established by nesting the malfunction inside its tool use case.
    parent_needs: tool_usecase
    violates: tool_req
```

The relationship is:

```{mermaid}
flowchart LR
    UC["tool_usecase"]
    PM["potential_tool_malfunction"]
    UP["upstream requirement"]
    TR["tool_req"]

    PM -->|"nested under<br/>(parent_needs)"| UC
    PM -->|"violates"| TR
    TR -->|"satisfies"| UP

    style UC fill:#E1D5E7
    style PM fill:#F8CECC
    style UP fill:#DAE8FC
    style TR fill:#F5F5F5
```

### What is a useful malfunction?

Describe **incorrect behaviour relevant to the use case**.

**Too generic:**

```text
The tool crashes.
The tool has a bug.
The tool produces a wrong result.
```

**Better:**

```text
An unresolved requirement link is accepted as valid.
A valid requirement is omitted from generated documentation.
Generated source code does not represent the configured input model correctly.
```

A useful question is:

> **What could the tool do incorrectly, or fail to do, such that one of the
> requirements we rely on is violated?**

### `violates`

Use `violates` for requirements whose expected behaviour is directly broken by
the malfunction.

Typical targets are:

- `tool_req`

### Tool model example

`````markdown
::::{tool_usecase} Validate requirement traceability during documentation builds
:id: tool_usecase__docs_as_code__traceability
:belongs_to: doc_tool__s_core_docs_as_code

The project relies on the documentation tool to detect invalid traceability.

:::{potential_tool_malfunction} Unresolved requirement link is accepted as valid
:id: potential_tool_malfunction__docs_as_code__unresolved_link_accepted
:violates:
  tool_req__docs_as_code__unresolved_links
:safety_affected: YES
:detection_sufficient: NO

An unresolved requirement link is accepted as valid and the documentation build
does not report the problem.
:::
::::
`````

There is no conceptual difference between external and self-developed tools in
this step. Malfunctions are derived from the intended usage and the tool
capabilities relevant to that usage.

`detection_sufficient` is only required in case of `safety_affected: YES`. A
safety-relevant malfunction with `detection_sufficient: YES` must also document a
non-empty `safety_measures` value. The malfunction body remains the place for the
human-readable reasoning that explains why the measure is sufficient or insufficient.

The same `tool_req` may be relevant to multiple use cases;
evaluate its potential malfunctions separately for each usage context.

---

## Step 4 — Evaluate safety impact and detection

For each `potential_tool_malfunction`, answer two questions.

### Does the malfunction affect safety?

Use:

```text
:safety_affected: YES
```

if the malfunction can:

- introduce an error into safety-related work, or
- prevent an existing error from being detected.

Use:

```text
:safety_affected: NO
```

if the malfunction has no relevant safety impact in this usage context.

This is a property of the **usage context and malfunction**, not a generic label
for the tool.

The same tool can therefore have safety-relevant and non-safety-relevant use
cases.

---

### Is detection sufficient?

`detection_sufficient` asks:

> **If this malfunction occurs during the intended use of the tool, do the
> measures that are part of that intended usage prevent or detect it with
> sufficient confidence?**

These measures can be:

- internal to the tool,
- provided by another tool,
- part of the surrounding workflow or process.

Examples include:

- generated source is compiled before integration,
- an independent consistency checker validates generated output,
- a review compares the generated artifact against its source,
- the tool performs an internal integrity check and rejects inconsistent input,
- a downstream tool independently validates critical information.

Document the relevant measure using `safety_measures`.

`````markdown
::::{tool_usecase} Generate production source from the approved model
:id: tool_usecase__generator__generate_source
:belongs_to: doc_tool__s_core_docs_as_code

:::{potential_tool_malfunction} Generated source contains invalid syntax
:id: potential_tool_malfunction__generator__invalid_syntax
:violates: tool_req__generator__valid_source
:safety_affected: YES
:detection_sufficient: YES
:safety_measures: Generated source is compiled before it can be integrated.

The generator may emit syntactically invalid source code. The mandatory
downstream compilation detects this malfunction before the output can be used.
:::
::::
`````

The important point is that the measure is part of the **defined intended
usage**.

It does not matter whether the measure existed before the TVR was written or
was introduced as a result of the evaluation. If it becomes a mandatory part of
the intended usage, evaluate the malfunction with that usage concept.

---

## Step 5 — Determine classification and qualification need

For the SCORE safety evaluation, the simplified decision is:

```{mermaid}
flowchart TD
    A{"safety_affected?"}
    A -->|"NO"| B["HIGH confidence<br/>No qualification required"]
    A -->|"YES"| C{"detection_sufficient?"}
    C -->|"YES"| B
    C -->|"NO"| D["LOW confidence<br/>Qualification required"]
```

| `safety_affected` | `detection_sufficient` | TVR SCORE TCL | Qualification |
|---|---|---|---|
| `NO` | not relevant | `HIGH` | not required |
| `YES` | `YES` | `HIGH` | not required |
| `YES` | `NO` | `LOW` | required |

The workflow automatically calculates the TVR summary from the owned
malfunction graph:

1. It follows `doc_tool` -> `tool_usecase` through the mandatory `belongs_to`
   link.
2. It follows each use case -> nested `potential_tool_malfunction` needs
   through the generated `parent_needs` relationship.
3. It reports safety affected as `YES` if any owned malfunction is safety
   affected; otherwise it reports `NO`.
4. It reports SCORE TCL as `LOW` if any owned malfunction is safety affected
   and has `detection_sufficient: NO`; otherwise it reports `HIGH`.

The generated report exposes the classification result as `HIGH` or `LOW`. In
this model, `HIGH` means no qualification is required and `LOW` means
qualification is required. A `LOW` result identifies the evidence that must be
provided; it does not mean that qualification has already happened. The
evaluation result and `detection_sufficient` remain unchanged by qualification.

After the evaluation is complete, the generated report exposes the derived
summary. No manual `safety_affected` or `tcl` values are required on the
`doc_tool`.

```text
:status: evaluated
SCORE TCL: HIGH
Qualification required: NO
```

or:

```text
:status: evaluated
SCORE TCL: LOW
Qualification required: YES
```

For a `LOW` result, the generated qualification view identifies the required
tool requirements and their current evidence status.

### Multiple use cases and malfunctions

The overall TVR result must reflect the relevant worst case.

If any safety-relevant malfunction has insufficient detection, the tool cannot
be treated as `HIGH` merely because the other use cases are well protected.

---

## Step 5a — Improve the usage concept instead of qualifying

A `LOW` evaluation does not mean qualification is the only possible response.

You may change the intended usage by adding an appropriate detection or
prevention measure.

```{mermaid}
flowchart LR
    subgraph Before
        A1["Generator"] --> A2["Generated output"]
        A2 --> A3["Used directly"]
    end

    subgraph After
        B1["Generator"] --> B2["Generated output"]
        B2 --> B3["Independent check"]
        B3 --> B4["Accepted output"]
    end
```

Before:

```text
:safety_affected: YES
:detection_sufficient: NO
```

An **independent check** is a separate opportunity to prevent or detect the
failure; it may be a downstream tool, compiler, consistency check, or review and
does not require a different organisation.

After the independent check becomes a mandatory part of intended usage:

```text
:safety_affected: YES
:safety_measures: Independent checker validates every generated artifact.
:detection_sufficient: YES
```

This requires **re-evaluating the affected malfunction because the usage concept
changed**.

The check must be mandatory for every applicable artifact or execution and gate
acceptance. Verify this through workflow or test-campaign evidence, such as a
CI gate, configured checker, or recorded review, and describe it in
`safety_measures`. An occasional or merely proposed check is insufficient.

It is not a reclassification caused by qualification.

---

## Step 6 — Qualify the tool if required

Qualification is an evidence activity required when the evaluation results in
insufficient confidence and the project does not resolve that through a changed
usage concept. It does not happen merely because the qualification view is
generated.

SCORE uses validation of the software tool as the qualification approach.

The qualification view starts from `tool_req`:

```{mermaid}
flowchart LR
    TR["tool_req"]
    TC["testcase"]
    RESULT["Test result / evidence"]

    TC -->|"fully_verifies or<br/>partially_verifies"| TR
    TC --> RESULT

    style TR fill:#F5F5F5
```

In the current S-CORE Docs-as-Code model, test execution results are represented
as `testcase` needs. Their normal links to requirements are:

- `fully_verifies`
- `partially_verifies`

For each qualification-relevant `tool_req`, qualification requires at least one
recorded testcase with `result: passed` and a `fully_verifies` link to that
requirement. A `partially_verifies` link is useful supplemental traceability,
but does not complete qualification by itself.

### Qualification is not a detection measure

Compare the two roles:

```{mermaid}
flowchart TB
    subgraph Usage["Detection during intended tool usage"]
        U1["Tool execution"] --> U2["Output"]
        U2 --> U3["Independent / internal check"]
        U3 --> U4["Output accepted"]
    end

    subgraph Qualification["Qualification evidence"]
        Q1["Specific tool version"] --> Q2["Requirements-based testcase"]
        Q2 --> Q3["Evidence that tool_req is satisfied"]
    end
```

A qualification testcase answers:

> Does this tool version satisfy the requirement?

A safety measure used for `detection_sufficient` answers:

> If the malfunction happens during real intended usage, will it be prevented or
> detected before its result is relied upon?

In other words, a qualification test checks whether the tool version satisfies
a `tool_req`. `detection_sufficient` checks whether the measures used during
normal tool usage will detect or prevent a malfunction before its output is
relied upon. Passing a qualification test therefore does **not** by itself
justify setting `detection_sufficient: YES`.

The same technical check can only count for both if it actually performs both
roles.

---

### External tool qualification

External tools are commonly validated largely as black boxes.

Example requirement:

````markdown
```{tool_req} Report unresolved requirement links
:id: tool_req__docs_as_code__unresolved_links

The tool shall report an unresolved requirement link as an error.
```
````

This is an example of a requirements-based qualification test; other campaign
tests need not be requirements-based:

1. create input containing a known unresolved link,
2. execute the configured tool version with the relevant configured invocation,
3. verify that the expected error is reported.

The campaign shall record the exact tool version, relevant configuration,
environment and dependencies, invocation, input, expected and actual results,
and outcome.

The resulting SCORE `testcase` must link to the tool requirement via
`fully_verifies` for the requirement to count as qualified. A
`partially_verifies` link may be recorded as supplemental evidence, but does not
complete qualification by itself.

Vendor documentation, release notes, and **upstream tests**—tests maintained
by the vendor or originating project—can support the argument. They remain
supporting information unless accepted under the recorded conditions and traced
to the relevant `tool_req`.

---

### Self-developed tool qualification

For a self-developed tool, do not automatically create a separate qualification
test suite.

If the normal development process already produces testcases that:

- verify the relevant `tool_req` needs,
- execute against the tool version being qualified,
- provide a recorded `result: passed`, and
- link to each relevant requirement with `fully_verifies`,

reuse those testcases as qualification evidence.

Prefer:

```{mermaid}
flowchart LR
    TR["Existing tool_req"] --> IMPL["Tool implementation"]
    TC["Existing testcase"] -->|"fully_verifies / partially_verifies"| TR
    TC --> E["Existing test evidence"]
```

over duplicating the same requirement and test solely for qualification.

Additional qualification tests are needed only where the existing evidence is
insufficient.

---

## Step 7 — Update the Tool Verification Report

If no qualification was required, the evaluated report can proceed to review.

If qualification was required and every relevant `tool_req` has the required
passed `fully_verifies` evidence, set the report status to `qualified`.

The evaluation result itself does **not** automatically change.

Changing the status does not create qualification evidence; it records that the
required evidence has already been provided.

This is a valid final state before release; the generated summary remains LOW:

```text
:status: qualified
```

`LOW` records why qualification was necessary.

`qualified` records that the additional qualification evidence has been
provided.

Qualification does not turn:

```text
:detection_sufficient: NO
```

into:

```text
:detection_sufficient: YES
```

unless the intended usage was also changed by introducing a new mandatory
detection mechanism.

---

## Step 8 — Review and release the Tool Verification Report

Review the completed TVR against the SCORE Tool Verification Report Review
Checklist.

The review shall describe, where applicable:

- unique tool identification,
- exact tool version and the relevant test-campaign execution conditions,
- purpose and tool use cases,
- inputs and outputs,
- configuration,
- environment and limitations,
- documentation,
- usage constraints,
- potential malfunctions,
- safety impact,
- safety measures,
- error detection,
- overall confidence,
- qualification evidence where required.

After successful approval:

```text
:status: released
```

If verification is unsuccessful:

```text
:status: rejected
```

See:

- [SCORE Tool Management Workflow](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/tool_management_workflow.html)
- [SCORE Tool Verification Report Template](https://eclipse-score.github.io/process_description/main/folder_templates/tools/tool_verification_report_template.html)
- [SCORE Tool Management Process Requirements](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/guidance/tool_management_reqs.html)
- [SCORE Tool Verification Report Review Checklist](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/guidance/tool_management_checklist.html)

---

## Complete example — external tool

Assume an external documentation tool is used to validate requirement
traceability.

### Upstream requirement

An upstream requirement is represented by a concrete SCORE requirement type, such
as `stkh_req`, `gd_req`, `feat_req`, or `comp_req`. This example uses the
existing `stkh_req` type:

````markdown
```{stkh_req} Provide valid verification traceability
:id: stkh_req__docs_as_code__traceability
:reqtype: Process
:safety: ASIL_B
:security: NO
:status: valid
:rationale: Invalid traceability can hide missing verification.
:valid_from: v1.0

Safety-related requirements shall have valid verification traceability.
```
````

### Tool requirement

````markdown
```{tool_req} Report unresolved requirement links
:id: tool_req__docs_as_code__unresolved_links
:satisfies: stkh_req__docs_as_code__traceability

The tool shall report unresolved requirement links as errors.
```
````

### Tool use case and potential malfunction

`````markdown
::::{tool_usecase} Validate requirement traceability during documentation builds
:id: tool_usecase__docs_as_code__traceability
:belongs_to: doc_tool__s_core_docs_as_code

The project relies on the documentation tool to detect invalid traceability
before generated documentation is accepted.

:::{potential_tool_malfunction} Unresolved requirement link is accepted as valid
:id: potential_tool_malfunction__docs_as_code__unresolved_link_accepted
:violates:
  tool_req__docs_as_code__unresolved_links
:safety_affected: YES
:detection_sufficient: NO

An unresolved requirement link is accepted as valid and no error is reported.
:::
::::
`````

The resulting model is:

```{mermaid}
flowchart LR
    UP["stkh_req__docs_as_code__traceability"]
    UC["tool_usecase__docs_as_code__traceability"]
    TR["tool_req__docs_as_code__unresolved_links"]
    PM["potential_tool_malfunction__docs_as_code__<br/>unresolved_link_accepted"]

    PM -->|"nested under<br/>(parent_needs)"| UC
    PM -->|"violates"| TR
    TR -->|"satisfies"| UP

    style UP fill:#DAE8FC
    style UC fill:#E1D5E7
    style TR fill:#F5F5F5
    style PM fill:#F8CECC
```

Because the malfunction is safety relevant and detection is insufficient:

```text
SCORE TCL = LOW
qualification required = YES
```

Qualification then validates
`tool_req__docs_as_code__unresolved_links`.

The resulting test execution must produce a `testcase` that links to the tool
requirement using the normal SCORE verification links, for example
`fully_verifies`.

The TVR remains `LOW`, but after successful qualification its lifecycle can
progress:

```{mermaid}
flowchart LR
    A["evaluated<br/>SCORE TCL = LOW"] --> B["qualification tests pass"]
    B --> C["qualified<br/>SCORE TCL = LOW"]
    C --> D["released<br/>SCORE TCL = LOW"]
```

---

## Complete example — self-developed tool

Assume the project develops its own model-to-code generator.

### Existing requirements

````markdown
```{stkh_req} Generate software from the approved model
:id: stkh_req__generator__approved_model
:reqtype: Functional
:safety: ASIL_B
:security: NO
:status: valid
:rationale: Production code must represent the approved behavioural model.
:valid_from: v1.0

Software source shall be generated from the approved model.
```
````

````markdown
```{tool_req} Preserve configured state transitions
:id: tool_req__generator__state_transitions
:satisfies: stkh_req__generator__approved_model

The generator shall preserve configured state transitions in generated source
code.
```
````

### Tool use case and potential malfunction

`````markdown
::::{tool_usecase} Generate production source from the approved model
:id: tool_usecase__generator__generate_source
:belongs_to: doc_tool__s_core_docs_as_code

The project relies on the generator to transform the approved model into
production source code.

:::{potential_tool_malfunction} State transition is omitted from generated source
:id: potential_tool_malfunction__generator__missing_transition
:violates:
  tool_req__generator__state_transitions
:safety_affected: YES
:detection_sufficient: NO

A state transition present in the approved input model is omitted from the
generated source code.
:::
::::
`````

Result:

```text
SCORE TCL = LOW
qualification required = YES
```

If an existing requirements-based test already verifies
`tool_req__generator__state_transitions` for the released generator version,
reuse its generated `testcase` and test evidence for qualification.

Do not create another requirement and another test solely to label them
"qualification".

---

## When to evaluate the tool again

Re-evaluate affected malfunctions when information used by the evaluation
changes.

Typical triggers include:

- a new or changed tool use case,
- new or changed upstream requirements (`stkh_req`, `gd_req`, `feat_req`, or `comp_req`),
- new or changed tool requirements,
- a changed tool version,
- a changed relevant configuration,
- a changed integration/environment,
- a newly identified potential malfunction,
- a new, changed, or removed safety measure,
- a changed surrounding workflow/toolchain,
- evidence that a previously sufficient detection measure is no longer
  sufficient.

Do **not** re-evaluate merely because qualification tests passed.

Qualification adds evidence about the tool. It does not by itself change the
intended usage or the detection measures.

```{mermaid}
flowchart TD
    A{"What changed?"}

    A -->|"Tool version / use case / requirement /<br/>workflow / safety measure"| B["Re-evaluate affected malfunctions"]
    A -->|"Only qualification tests executed"| C["No re-evaluation required"]

    B --> D["Update TVR evaluation if result changed"]
```

---

## Common mistakes

### Treating `tool_usecase` as a new requirement level

Do not invent new normative behaviour in `tool_usecase`.

A `tool_usecase` describes how the project uses the tool. A `tool_req` describes
a capability or behaviour provided by the tool, regardless of whether the project
uses it in a particular use case. The use case provides context and grouping
without introducing an additional normative requirement level.

For example, "validate requirement traceability during
documentation builds" is a use case; "the tool shall report unresolved links"
is the tool requirement.

Another example is the pair of use cases "Produce the platform components binaries"
and "Create unit test binaries", which both map to the tool requirement
"the compiler shall create an executable from C++ source code".

The use case adds context, not another requirement level.

```{mermaid}
flowchart LR
    UP["Upstream requirement"]
    UC["Usage context"]
    TR["Concrete tool behaviour"]

    TR -->|"satisfies"| UP
```

---

### Using generic malfunctions

Avoid:

```text
The tool crashes.
The tool has a bug.
The result is wrong.
```

Prefer:

```text
A missing link is accepted as valid.
A required artifact is omitted from generated output.
The generated value differs from the configured source value.
```

---

### Treating every existing test as a safety measure

A test executed during development or release validation is not automatically a
measure for `detection_sufficient`.

Development and qualification tests provide evidence about a tool version;
detection sufficiency requires a mechanism that runs during intended use and
prevents or detects the malfunction before the result is relied upon. Therefore,
adding a campaign test does not by itself make detection sufficient.

Ask:

> If the malfunction occurs during actual intended tool usage, does this
> mechanism prevent or detect it before the result is relied upon?

If not, it is not sufficient justification for:

```text
:detection_sufficient: YES
```

---

### Treating qualification as reclassification

Qualification may leave the evaluation unchanged:

```text
:safety_affected: YES
:detection_sufficient: NO
:status: qualified
```

This is not contradictory.

`LOW` describes the evaluation.

`qualified` describes the additional evidence.

---

### Duplicating external specifications

Do not copy an external tool's complete specification into `tool_req`.

Do not copy almost the entire external C&Q or qualification specification from
the Internet either; capture only the capabilities and assumptions relevant to
the evaluated use cases.

Model the tool capability being evaluated; describe the project context in the
corresponding `tool_usecase`.

---

### Duplicating self-developed tests

Do not build a parallel qualification-test world when existing SCORE testcases
already verify the relevant `tool_req` needs with suitable evidence.

---

## Quick reference

```{mermaid}
flowchart TD
    A["1. Identify exact tool version / configuration"]
    B["2. Create doc_tool<br/>status = draft"]
    C["3. Define tool_usecase"]
    D["4. Link available tool_req<br/>to upstream requirements"]
    E["5. Identify potential_tool_malfunction"]
    F["6. Read generated TVR summary"]
    G["7. Document safety_measures<br/>and detection_sufficient"]
    H["8. Read generated SCORE TCL"]
    I["status = evaluated"]
    J{"SCORE TCL = LOW?"}
    K["Verify relevant tool_req<br/>with testcase evidence"]
    L["status = qualified"]
    M["Review / approve TVR"]
    N["status = released"]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J
    J -->|"No"| M
    J -->|"Yes"| K --> L --> M
    M --> N
```

In short:

```text
tool_usecase
    -> defines the context in which we rely on the tool

potential_tool_malfunction
    -> describes how that reliance can fail

safety_affected
    -> says whether the failure matters for safety

safety_measures + detection_sufficient
    -> describe whether intended usage prevents/detects the failure

LOW
    -> qualification is required

testcase -> fully_verifies/partially_verifies -> tool_req
    -> provides qualification evidence

qualified
    -> qualification evidence exists; it does not change the generated SCORE TCL
```

## SCORE references

- [Tool Management Workflow](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/tool_management_workflow.html)
- [Tool Verification Report Template](https://eclipse-score.github.io/process_description/main/folder_templates/tools/tool_verification_report_template.html)
- [Tool Management Process Requirements](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/guidance/tool_management_reqs.html)
- [Tool Verification Report Review Checklist](https://eclipse-score.github.io/process_description/main/process_areas/tool_management/guidance/tool_management_checklist.html)

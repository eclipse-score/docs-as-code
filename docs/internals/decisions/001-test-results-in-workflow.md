:::{dec_rec} Decision Record 001: Test results in Docs-As-Code Workflows
:id: dec_rec__dac__001_test_results_in_workflows
:status: accepted
:context: Need to embed test results into docs, but tests are slow.
:decision: Run quick docs checks and tests in parallel, then full docs generation sequentially.
:consequences: implementation effort
:::

# Decision Record 001: Test results in Docs-As-Code Workflows

## Goals

* PR
  * Early detection of issues
  * Generate website-preview
* Post-Merge
  * Generate website

## Problem Statement

Some parts of generating docs are rather slow:
1) Embedding test results, implies that we need test results
2) Generating HTML output, especially generating diagrams (PlantUML)

Note: the used tools are irrelevant for the problem statement.

## Current Situation

```{mermaid}
flowchart TD
 subgraph subGraph0["Pre-Merge Workflow"]
        parallel["parallel"]
        PR["Pull Request<br>"]
        DOCS1["HTML Build<br>&lt;slow&gt;"]
        TESTS["tests<br>&lt;slow&gt;"]
        WP1["Website Preview"]
        TF2["PR Feedback"]
  end
 subgraph subGraph1["Post-Merge Workflow"]
        DOCS2["HTML Build<br>&lt;slow&gt;"]
        PM["Post-Merge<br>"]
        W["Website"]
  end
    PR --> parallel
    parallel --> DOCS1 & TESTS
    DOCS1 --> WP1
    TESTS --> TF2
    PM --> DOCS2
    DOCS2 --> W

    parallel@{ shape: fork}
    PR@{ shape: event}
    DOCS1@{ shape: lean-l}
    TESTS@{ shape: out-in}
    WP1@{ shape: stored-data}
    TF2@{ shape: stored-data}
    DOCS2@{ shape: lean-l}
    PM@{ shape: event}
    W@{ shape: stored-data}
```


## Solution

A combination of test and docs workflows:

```{mermaid}
flowchart TD
 subgraph subGraph0["Pre-Merge Workflow"]
        DC["Docs Verification<br>&lt;fast&gt;"]
        DCF["PR Feedback"]
        PR["Pull Request"]
        T1["tests<br>&lt;slow&gt;"]
        TF["PR Feedback"]
        HB1["HTML Build<br>&lt;slow&gt;"]
        WP["Website Preview"]
        parallel["parallel"]
  end
 subgraph subGraph1["Post-Merge Workflow"]
        T2["tests"]
        PM["Post-Merge"]
        HB2["HTML Build"]
        W["Website"]
  end

DC --> DCF
DC -- cache --> HB1
T1 -- results --> HB1
T1 --> TF
HB1 --> WP
PR --> parallel
parallel --> DC & T1

PM --> T2
T2 --> HB2
HB2 --> W

PR@{ shape: event}

DC@{ shape: out-in}
T1@{ shape: out-in}
HB1@{ shape: out-in}
parallel@{ shape: fork}
TF@{ shape: stored-data}
WP@{ shape: stored-data}
DCF@{ shape: stored-data}

PM@{ shape: event}
W@{ shape: stored-data}
T2@{ shape: out-in}
HB2@{ shape: out-in}
```

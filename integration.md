# Integration Testing in a Distributed Monolith

*RFC – Working draft. High-level overview of how our projects typically integrate (reflecting practices used in several codebases). Assumptions and trade-offs are noted; please flag gaps or over-complication so we can iterate. Easiest way for feedback is face to face!*

Teams often split what is functionally a single system across many repositories. Each repository can show a green build while the assembled system is already broken. This article looks at how to bring system-level feedback earlier when you work that way. This article does not argue for pull requests, trunk-based development, or continuous integration itself. Those are well covered elsewhere. It also does not look into any specific tools or implementations for achieving these practices - except for providing a GitHub based example.

The context here assumes three things: you develop through pull requests with required checks; you have multiple interdependent repositories that ship together; and you either have or will create a central integration repository used only for orchestration. If any of those are absent you will need to establish them first; the rest of the discussion builds on them.

## Where Problems Usually Appear
An interface change (for example a renamed field in a shared schema) is updated in two direct consumers. Their pull requests pass. Another consumer several repositories away still depends on the old interface and only fails once the whole set of changes reaches main and a later integration run executes. The defect was present early but only visible late. Investigation now needs cross-repo log hunting instead of a quick fix while the change was still in flight.

Running full end-to-end environments on every pull request is rarely affordable. Coordinated multi-repository changes are then handled informally through ad-hoc ordering: “merge yours after mine”. Late detection raises cost and makes regression origins harder to locate.

## Core Ideas
We model the integrated system as an explicit set of (component, commit) pairs captured in a manifest. We derive those manifests deterministically from events: a single pull request, a coordinated group of pull requests, or a post-merge refresh. We run a curated fast subset of integration tests for pre-merge feedback and a deeper suite after merge. When a suite passes we record the manifest (“known good”). Coordinated multi-repository changes are treated as a first-class case so they are validated as a unit rather than through merge ordering.

## Terminology
Component – a repository that participates in the assembled product (for example a service API repo or a common library).
Fast subset – a curated group of integration tests chosen to finish in single-digit minutes; for example tests that exercise protocol seams or migration boundaries.
Tuple – the mapping of component names to their commit SHAs for one integrated build; e.g. { users: a1c3f9d, billing: 9e02b4c }.
Known good – a tuple plus metadata (timestamp, suite, manifest hash) that passed a defined suite and is stored for later reproduction.


## A Note on History
Classic continuous integration advice assumed a single codebase. Splitting a cohesive system across repositories reintroduces many of the coordination issues CI was meant to remove. The approach here adapts familiar CI principles (frequent integration, fast feedback, reproducibility) to a multi-repository boundary.

## Why Use a Central Integration Repository
A central repository offers a neutral place to define which components participate, to build manifests from events, to hold integration‑specific helpers (overrides, fixtures, seam tests), and to persist records of successful tuples. It should not contain business code. Keeping it small keeps review focused and reduces accidental coupling.

## Workflow Layers
We use three recurring workflows: a single pull request, a coordinated subset when multiple pull requests must land together, and a post‑merge fuller suite. Each produces a manifest, runs an appropriate depth of tests, and may record the tuple if successful.

### Single Pull Request
When a pull request opens or updates, its repository runs its normal fast tests. The integration repository is also triggered with the repository name, pull request number, and head SHA. It builds a manifest using that SHA for the changed component and the last known-good (or main) SHAs for others, then runs the curated fast subset. The result is reported back to the pull request. The manifest and logs are stored even when failing so a developer can reproduce locally.

The subset is explicit rather than dynamically inferred. Tests in it should fail quickly when contracts or shared schemas drift. If the list grows until it is slow it will either be disabled or ignored; regular curation keeps it useful.

### Coordinated Multi-Repository Subset
Some changes require multiple repositories to move together (for example a schema evolution, a cross-cutting refactor, a protocol tightening). We mark related pull requests using a stable mechanism such as a common label (e.g. changeset:feature-x). The integration workflow discovers all open pull requests sharing the label, builds a manifest from their head SHAs, and runs the same fast subset. A unified status is posted back to each pull request. None merge until the coordinated set is green. This removes informal merge ordering as a coordination mechanism.

### Post-Merge Full Suite
After merges we run a deeper suite. Some teams trigger on every push to main; others run on a schedule (for example hourly). Per-merge runs localise failures but cost more; batched runs save resources but expand the search space when problems appear (for example every two hours when resources are constrained). When the suite fails, retaining the manifest lets you bisect between the last known-good tuple and the current manifest (using a scripted search across the changed SHAs if multiple components advanced). On success we append a record for the tuple with a manifest hash and timing data.

### Manifests
Manifests are minimal documents describing the composition. They allow reconstruction of the integrated system later.

Single pull request example:
```
pr: 482
component_under_test:
  name: docs-as-code
  repo: eclipse-score/docs-as-code
  sha: 6bc901f2
others:
  - name: component-a
    repo: eclipse-score/component-a
    ref: main
  - name: component-b
    repo: eclipse-score/component-b
    ref: main
subset: pr_fast
timestamp: 2025-08-13T12:14:03Z
```

Coordinated example:
```
components:
  - name: users-service
    repo: eclipse-score/users-service
    branch: feature/new_email_index
    pr: 16
  - name: auth-service
    repo: eclipse-score/auth-service
    branch: feature/lenient-token-parser
    pr: 150
others:
  - name: billing-service
    repo: eclipse-score/billing-service
    ref: last_stable
subset: pr_fast
changeset: feature-x
```

Large configuration belongs elsewhere; manifests should stay readable and diffable.

## GitHub Realisation
*Conceptual outline; not yet implemented here.*

Trigger from a component repository:
```
name: integration-pr
on: [pull_request]
jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Dispatch to integration repo
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.INTEGRATION_TRIGGER_TOKEN }}
          repository: eclipse-score/reference_integration
          event-type: pr-integration
          client-payload: >-
            {"repo":"${{ github.repository }}","pr":"${{ github.event.pull_request.number }}","sha":"${{ github.sha }}"}
```

Integration repository receiver (subset):
```
on:
  repository_dispatch:
    types: [pr-integration]
jobs:
  pr-fast-subset:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Parse payload
        run: echo '${{ toJson(github.event.client_payload) }}' > payload.json
      - name: Materialize composition
        run: python scripts/gen_pr_manifest.py payload.json manifest.pr.yaml
      - name: Fetch component under test
        run: python scripts/fetch_component.py manifest.pr.yaml
      - name: Render MODULE overrides
        run: python scripts/render_overrides.py manifest.pr.yaml MODULE.override.bzl
      - name: Bazel test (subset)
        run: bazel test //integration/subset:pr_fast --override_module_files=MODULE.override.bzl
      - name: Store manifest & results
        uses: actions/upload-artifact@v4
        with:
          name: pr-subset-${{ github.run_id }}
          path: |
            manifest.pr.yaml
            bazel-testlogs/**/test.log
```

Post-merge full suite:
```
on:
  schedule: [{cron: "15 * * * *"}]
  repository_dispatch:
    types: [component-merged]
jobs:
  full-suite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate full manifest
        run: python scripts/gen_full_manifest.py manifest.full.yaml
      - name: Bazel test (full)
        run: bazel test //integration/full:all --test_tag_filters=-flaky
      - name: Persist known-good tuple (on success)
        if: success()
        run: python scripts/persist_tuple.py manifest.full.yaml known_good/index.json
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: full-${{ github.run_id }}
          path: |
            manifest.full.yaml
            known_good/index.json
            bazel-testlogs/**/test.log
```

### Recording Known-Good Tuples
Known-good records are stored append-only.
```
[
  {
    "timestamp": "2025-08-13T12:55:10Z",
    "tuple": {
      "docs-as-code": "6bc901f2",
      "component-a": "91c0d4e1",
      "component-b": "a44f0cd9"
    },
    "manifest_sha256": "4c9b7f...",
    "suite": "full",
    "duration_s": 742
  }
]
```
Persisting enables reproduction (attach manifest to a defect), audit (what exactly passed before a release), gating (choose any known-good tuple), and comparison (diff manifests to isolate drift) without relying on (rather fragile) links to unique runs in your CI system.

## Curating the Fast Subset
Tests in the subset need to fail quickly when public seams change. Keep the list explicit (an alias such as //integration/subset:pr_fast). Remove redundant tests and quarantine flaky ones; otherwise the feedback loop becomes noisy or slow. Review the subset periodically (for example monthly or after significant interface churn) to keep its signal-to-noise high.

## Handling Failures
For a failing pull request subset: inspect the manifest and failing log; reproduce locally with a script that consumes the manifest. For a failing coordinated set: treat all participating pull requests as a unit and address seam failures before merging any. For a failing post-merge full suite: bisect between the last known-good tuple and the current manifest (script permutations when more than one repository changed) to narrow the cause. Distinguish between a genuine regression and test fragility so you do not mask product issues by disabling tests.

## Trade-offs and Choices
Using manifests and commit SHAs instead of assigning semantic versions to every commit keeps validation close to current heads without creating tag noise. A two-tier arrangement (subset and full) offers a clear mental model; more tiers can be added later if evidence supports them. A central orchestration repository centralises caching and secrets handling and keeps audit history straightforward.

## Practical Notes
Cache builds to stabilise subset runtime. Hash manifests (e.g. SHA-256) to reference runs succinctly. Provide an endpoint or badge showing the most recent known-good tuple. Generate overrides rather than editing them manually. Optionally lint the subset target to ensure only approved directories are referenced.

## Avoiding Common Pitfalls
Selecting tests dynamically from a diff often misses schema or contract drift. Editing integration configuration manually for individual pull requests produces runs that cannot be reproduced. Relying on merge order to coordinate a multi-repository change delays detection to the last merger.

## Signs It Is Working
An interface change that would break another repository fails in the subset run before merge. A coordinated schema change shows a unified status across all related pull requests. A regression introduced over several independent merges is detected by the full suite and localised quickly using stored manifests.

## Summary
By expressing the integrated system as explicit manifests, curating a fast integration subset for pull requests, and running a deeper post-merge suite, you move discovery of cross-repository breakage earlier while keeping costs predictable. Each successful run leaves a reproducible record, making release selection and debugging straightforward. The approach lets a distributed codebase behave operationally like a single one.

*Further reading:* Continuous Integration (Fowler), Continuous Delivery (Humble & Farley), trunk-based development resources.

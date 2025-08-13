# Integration Testing Workflows in Distributed Monoliths

## Introduction

This article assumes you already: (1) develop via pull requests with required checks; (2) work across multiple interdependent repositories (a distributed monolith); and (3) have a central integration repository that orchestrates cross‑component builds and tests. We treat those as prerequisites—not topics to justify.

The focus is on tightening workflows: fast pre‑merge signals, coordinated multi‑repo change handling, and post‑merge validation that produces auditable, reproducible version tuples. We skip foundational explanations and concentrate on practice.

---

## Prerequisites

This article assumes familiarity with modern software engineering practices, particularly:

- CI/CD principles
- Git‑based workflows (feature branches, pull requests, rebases, merges)

For foundational material, see:

- [Modern Software Engineering – David Farley](https://www.oreilly.com/library/view/modern-software-engineering/9780137314942/)
- [Continuous Delivery – Jez Humble & David Farley](https://www.oreilly.com/library/view/continuous-delivery-reliable/9780321670250/)
- [The DevOps Handbook – Gene Kim, Patrick Debois, John Willis, and Jez Humble](https://www.oreilly.com/library/view/the-devops-handbook/9781098182281/)
- [Continuous Integration – Martin Fowler](https://martinfowler.com/articles/continuousIntegration.html)
- [The Continuous Delivery YouTube Channel](https://www.youtube.com/c/ContinuousDelivery)
- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
- [Applying Trunk-Based Development in Large Teams](https://www.linkedin.com/blog/engineering/optimization/continuous-integration)
- [End-to-End Testing for Microservices – Bunnyshell](https://www.bunnyshell.com/blog/end-to-end-testing-for-microservices-a-2025-guide)
- [Scaling Distributed CI/CD Pipelines – ResearchGate](https://www.researchgate.net/publication/390157984_Scaling_Distributed_CICD_Pipelines_for_High-Throughput_Engineering_Teams_Architecture_Optimization_and_Developer_Experience)

---

## Glossary

- **Component**: A self-contained unit of code, typically a library or binary, that integrates with other components.
- **Component Test**: Tests a single component in isolation.
- **Integration Test**: Validates interactions between multiple components or subsystems.
- **Fast Tests**: Tests designed to execute in under ten minutes, providing rapid feedback.

---

## Scope

This article does not address:

- The rationale for pull‑request–based workflows or distributed monoliths
- Specific CI/CD tooling
- Container orchestration or service mesh patterns
- Regulatory frameworks or compliance processes
- General testing theory

---

## The Challenge of Integration

Distributed monoliths look like microservices on paper—many repositories, many builds—but behave like a single system in practice. Components share APIs, schemas, and timing assumptions. They often ship together. A small change in one place can ripple across the rest.

Standard PR pipelines validate the piece you touched but often miss the system you implicitly changed. When components are tested in isolation, the first realistic system behavior appears post‑merge—after a change meets everyone else’s. That’s late and expensive feedback.

Component-level testing typically doe not include contract testing, with the implicit assumption that downstream integration tests will catch any issues. This undermines the fast feedback loops essential for effective development. Moreover, standard Git-based workflows validate only the changed component in isolation, not the integrated system. Coordinating changes across repositories is non-trivial, and integration failures often surface post-merge, when remediation is more disruptive.

1. End‑to‑end tests are slow and costly. Provisioning a realistic environment, compiling a build matrix, or coordinating hardware‑in‑the‑loop can push runtimes beyond what’s practical on every PR.
2. Cross‑repository changes are common. Interface tweaks, coordinated refactorings, or schema migrations need to move in lock‑step—even though Git’s default workflows don’t know that.

We need to bring system‑level validation forward without imposing heavy costs on every PR, and to coordinate multi‑repo changes as first‑class citizens—within a PR‑gated workflow.

---

## Goals and Architectural Approach

We focus on optimizing the existing setup. Effective integration workflows should:

- Provide early, actionable feedback at the component level
- Reliably and reproducibly test cross‑component integration
- Balance test cost with coverage depth
- Scale with pull‑request–driven workflows
- Maintain traceability and visibility into what was tested, when, and why

A central integration repository (assumed present) handles:

- Defining participating components
- Holding integration test configuration
- Triggering tests for explicit version combinations
- Recording/approving validated sets for downstream use

Benefits (realized when disciplined) include:

- Separation of concerns: the integration repository contains no application code, focusing solely on orchestration
- Efficient CI pipeline design: component pipelines are distinct from cross‑component integration pipelines, reducing redundant CI overhead
- Consistent governance: updates must pass defined quality checks before acceptance, preserving system integrity without impeding local agility
- Independent component repositories: each component evolves in its own repository, with isolated development and CI
- Minimal overhead: component repositories remain lightweight, free from unnecessary shared tooling
- Improved troubleshooting: failures can be isolated to individual components or integration logic, expediting root cause analysis

---

## Integration Workflows

### Pre‑Merge Testing (Pull Requests)

When a PR is opened or updated in a component repository, two parallel workflows are triggered:

- Fast, component‑specific tests (unit and component‑level integration) run in the component’s CI pipeline.
- A system‑level integration workflow in the integration repository validates compatibility with the rest of the system, typically running a fast subset of the integration test suite.

The integration repository fetches the PR branch from the component under test and combines it with the latest main branches (or last known‑good versions) of other components to form a synthetic system configuration. This configuration is then built and tested. The workflow may run in parallel with component CI (favoring rapid feedback) or sequentially (minimizing CI load), depending on project constraints.

---

### Pre‑Merge Testing of Cross‑Repository Dependent Changes

When changes in one component necessitate coordinated updates in others, the integration repository enables testing these combinations together. Related PRs across repositories are grouped, and the integration repository constructs a configuration using the relevant branches. Run the same fast subset as for single‑PR validation and report a unified status back to each PR.

Two conventions help:

- Group related PRs via metadata (titles, labels, or an explicit manifest) so the integration repo can discover them
- Resolve branch selection deterministically (e.g., PR branch overrides main for listed components; others stick to last known‑good)

This turns ad‑hoc coordination into a normal operation. It reduces the risk that “the last repo to merge” breaks the system because you tested the change set as a unit before anything merges.

---

### Post‑Merge Integration Validation

After a PR is merged, the integration repository runs a fuller integration suite using the updated state. Some teams run this on every main‑branch commit; others batch changes and run on a timer. Whatever the cadence, the goal is to run a deeper suite than the pre‑merge subset and to record the exact component versions that passed.

Two common patterns:

- Always‑on verification: run after every merge. Failures are easy to attribute but costs are higher.
- Scheduled verification: run on a timer. Costs are lower; root cause analysis is harder. Pair this with bisect automation to identify the offending change when failures occur.

Successful post‑merge tests confirm system stability, and the exact version tuple is recorded for future reference. This decouples verification from release, allowing components and the integrated system to be released independently as needed.

---

### Conclusion

Integrating distributed, component‑based systems in a PR‑driven workflow demands disciplined orchestration. Keep most checks close to the code. Use a central integration repository to assemble realistic compositions, run a fast subset pre‑merge, and verify deeply post‑merge. Record exactly what passed. Treat coordinated changes as first‑class. Over time, you’ll get what you need: quick PR feedback and confidence that the system still works when parts move.

---

## Considered Alternatives

### SemVer per Component

Each component could adopt Semantic Versioning (SemVer) independently, allowing for more granular control over versioning and dependencies. However in the end we want to verify main branches, and not tagged commits. Tagging every commit with a version number would be a rather silly replacement of git hashes.

---

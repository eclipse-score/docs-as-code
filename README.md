# docs-as-code

Docs-as-code tooling for Eclipse S-CORE

Full documentation is on [GitHub Pages](https://eclipse-score.github.io/docs-as-code/).

> [!NOTE]
> This repository offers a [DevContainer](https://containers.dev/).
> For setting this up read [eclipse-score/devcontainer/README.md#inside-the-container](https://github.com/eclipse-score/devcontainer/blob/main/README.md#inside-the-container).

## Development of docs-as-code

### Getting IDE support for docs-as-code development

Create the virtual environment via `bazel run //:ide_support`.
If your IDE does not automatically ask you to activate the newly created environment you can activate it.

- In VSCode via `ctrl+p` => `Select Python Interpreter` then select `.venv_docs/bin/python`
- In the terminal via `. .venv_docs/bin/activate`


### Enabeling pre-commit

Pre-commit is supported inside docs-as-code to help with code quality and make developers workflow easier.

Install the hook:
```bash
pre-commit install

# Or install it to run on pre-push via:
pre-commit install --hook-type pre-push
```

Execute the pre-commit manually via `pre-commit run` or `pre-commit run --all-files` to run it on all files.

## Sphinx-needs processing rules

> [!WARNING]
> These rules are currently a **work-in-progress / demonstration** and are not yet production ready.

In addition to building the documentation, docs-as-code ships a set of Bazel macros
(in [docs.bzl](docs.bzl), backed by the Python tools in [scripts_bazel/](scripts_bazel))
that post-process the `needs.json` produced by the documentation build. They let you:

- **Filter** `needs.json` down to selected element types and/or components
  (`filtered_needs_json`, plus convenience wrappers such as `component_requirements`,
  `feature_requirements`, `assumptions_of_use`, `feature_architecture`, `component_architecture`).
- **Render** the selected needs as a Markdown document (`sphinx_needs_to_md`).
- **Convert** S-CORE requirements into [TRLC](https://github.com/bmw-software-engineering/trlc)
  (`sphinx_needs_to_trlc`).
- **Validate checklists** by pinning a SHA256 hash on a `mod_insp` / `mod_ver_report`
  record and failing the build when the reviewed output drifts
  (`requirements_checklist`, `architecture_checklist`, `dfa_checklist`,
  `fmea_checklist`, `verification_report`).
- **Bundle** a component's or feature's checklists, docs and sub-components
  (`score_component`, `score_module`).

See [scripts_bazel/README_needs_rules.md](scripts_bazel/README_needs_rules.md) for the
full guide, including usage examples, transitive-dependency hashing and resolving
external needs via `extra_needs`.

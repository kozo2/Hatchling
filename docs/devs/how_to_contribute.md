# Contribution Guidelines: Versioning Automation

This article is about:

- Branch naming conventions for versioning
- Automated version tag updates
- Workflow behavior for documentation and CI/CD branches

Hatchling uses automated workflows to manage versioning. This guide describes how contributors should work with branches and version tags.

## General Instructions

The organization maintains general instructions for documentation, code style, testing, and other standards in the `.github/instructions/` directory. These instructions apply to all developers and must be provided as reference to any coding LLMs used for automation or code generation. Review these files for project-wide standards before contributing:

- `documentation.instructions.md`: Defines the style, tone, and structure for all markdown documentation, emphasizing technical clarity and conciseness.
- `python_docstrings.instructions.md`: Specifies the required format and content for Python docstrings, ensuring consistency and completeness in code documentation.
- `readme.instructions.md`: Outlines the standards for README files, including required sections and formatting for project overviews.
- `testing.instructions.md`: Details comprehensive testing guidelines, including test structure, coverage expectations, and reporting standards for all repositories.

## Branch Naming

- Use `feat/` for features, `fix/` for bug fixes, `dev` for integration.
- Use `docs/` for documentation and `cicd/` for CI/CD changes.
- Only `feat/`, `fix/`, `dev`, and `main` branches trigger automated version tag updates.
- Branches such as `docs/` and `cicd/` do not increment version tags or update version files until changes are merged into `dev`.

## Automated Versioning

See [versioning](./versioning.md).

- Pushes to `feat/`, `fix/`, `dev`, or `main` branches automatically update version files and publish tags according to workflow logic.
- Work in `docs/` and `cicd/` branches does not affect version tags; versioning resumes when merged into `dev`.
- Do not manually edit `VERSION` or `VERSION.meta`. All updates are handled by automation.

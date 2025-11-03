# Contributing Guide

How to set up, code, test, review, and release so contributions meet our Definition of Done.

## Code of Conduct

All contributors are expected to:
- Communicate respectfully in Discord and Outlook
- Actively listen and provide constructive feedback
- Follow our conflict resolution process:
    1. Address issues directly with the teammate within 48 hours 
    2. If unresolved, bring the issue to the next team meeting
    3. If the issue remains unresolved, escalate to the instructor.

## Getting Started

List prerequisites, setup steps, environment variables/secrets handling, and how to run the app locally.

- Python 3.8, 3.9, 3.10
- *Note* section will be updated as seen fit

## Branching & Workflow

- default branch: main
- branch naming: 
    - feature/<description> -> new features
    - fix/<issue-number>-<description> -> bug fixed
    - docs/<description> -> documents
- create a new branch for each task/issue
- commit often with meaningful messages
- merge into main only after approval and passing CI

## Issues & Planning

Explain how to file issues, required templates/labels, estimation, and triage/assignment practices.
- File issues using GitHub Issues tab and include:
    - summary of the problem
    - expected behavior
    - steps to reproduce issue
    - assigned member and due date
- Labels:
    - bug: defects or malfunctions
    - improve: improvements or enhancements
    - feature: new features
    - docs: README or doc updates
    - help: needs assistance
    - question: clarification or research topic 

## Commit Messages

State the convention (e.g., Conventional Commits), include examples, and how to reference issues.
- Format:
    - <type>(scope): short description
    - example: <feature>(visualization): add wildfire correlation plot
    - reference related issues with #<issue_number> when applicable

## Code Style, Linting & Formatting

Name the formatter/linter, config file locations, and the exact commands to check/fix locally.
- Linter: Pylint
- Config path: .github/workflows/pylint.yml
- name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pylint
    - name: Analysing the code with pylint
      run: |
        pylint $(git ls-files '*.py')

## Testing

Define required test types, how to run tests, expected coverage thresholds, and when new/updated tests are mandatory.

## Pull Requests & Reviews

Outline PR requirements (template, checklist, size limits), reviewer expectations, approval rules, and required status checks.

## CI/CD

Link to pipeline definitions, list mandatory jobs, how to view logs/re-run jobs, and what must pass before merge/release.

## Security & Secrets

State how to report vulnerabilities, prohibited patterns (hard-coded secrets), dependency update policy, and scanning tools.

## Documentation Expectations

Specify what must be updated (README, docs/, API refs, CHANGELOG) and docstring/comment standards.

## Release Process

Describe versioning scheme, tagging, changelog generation, packaging/publishing steps, and rollback process.

## Support & Contact

Provide maintainer contact channel, expected response windows, and where to ask questions.

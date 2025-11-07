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
    - feature/&lt;description&gt; -> new features
    - fix/&lt;issue-number&gt;-&lt;description&gt; -> bug fixed
    - docs/&lt;description&gt; -> documents
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
    - &lt;type&gt;(scope): short description
    - example: &lt;feature&gt;(visualization): add wildfire correlation plot
    - reference related issues with #&lt;issue_number&gt; when applicable

## Code Style, Linting & Formatting

- Linter: Pylint
- Config path: .github/workflows/pylint.yml
- name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pylint
    - name: Analyzing the code with pylint
      run: |
        pylint $(git ls-files '*.py')

## Testing

- all new or modified code must include tests in the /tests directory
- run tests with:
    pytest
- Requirements:
    - include unit and integration tests where applicable
    - maintain at least 80% test coverage
    - new tests are required for new features and bug fixes
    - all tests must pass locally and in CI before merge

## Pull Requests & Reviews

Outline PR requirements (template, checklist, size limits), reviewer expectations, approval rules, and required status checks.
- All contributions must go through a PR
- PRs must reference related issue numbers when applicable
- Each PR must:
    - pass all CI checks
    - include updated documentation if needed
    - receive at least one peer review approval
- Reviewer expectations:
    - provide feedback within 48 hours
    - verify code correctness, readability, and style
    - confirm all DoD criteria are met

## CI/CD

- Configured under .github/workflows
- Example log: GitHub Actions -> Wildfire Branch
- Mandatory jobs:
    - build: install dependencies and run tests
    - lint: run static analysis
    - docs: verify docs updated
- Merge to main is blocked until all jobs pass

## Security & Secrets

- Never commit sensitive credentials, API keys, or tokens
- Use .env files locally and keep them in .gitignore
- Report vulnerabilities privately to any member listed in the README.md file
- Security checks run automatically through CI using pip-audit
- dependencies should be reviewed and updated monthly

## Documentation Expectations

- All significant code or data change must include:
    - Updates to README.md (if setup changes)
    - Added/updated docs if relevant

## Release Process

- Versioning Scheme: MAJOR.MINOR.PATCH
- Tag releases as v1.0.0, v1.1.0, etc
- Generate changelog via GitHub Releases
- Ensure CI/CD passes before tagging a release
- If a release introduces issues, rollback by reverting to the last stable tag

## Support & Contact

- Primary Contacts via Outlook:
    - Umna Khawaja: khawajau@oregonstate.edu 
    - Evia Liang: liangev@oregonstate.edu
    - John Stryker: strykerj@oregonstate.edu 
- Response Time: Within 24 hours

# AI Notes

AI tools were used as development assistants throughout this project. I used **Claude/Claude Code**, **GitHub Copilot**, and **ChatGPT** for architecture discussion, implementation suggestions, debugging, and code review.

## How I used AI

**Claude / Claude Code** was primarily useful for higher-level and multi-file work: reviewing the temporal data model, discussing API and authorization design, evaluating database constraints, and reasoning about deployment and testing.

**GitHub Copilot** was primarily used inside the editor for smaller implementation tasks such as Angular components, Django/DRF boilerplate, serializers, views, and repetitive code.

**ChatGPT** was used for incremental implementation planning, debugging, reviewing architecture decisions, deployment troubleshooting, and identifying acceptance tests.

I treated AI output as a starting point rather than automatically accepting generated code.

## Examples where AI output needed correction

### 1. Importer assumed the wrong data model

An AI-generated importer initially treated strain information like a plain string. In the actual application, `Animal.strain` is a foreign key to `Strain`.

I reviewed the model and changed the importer to resolve the existing `Strain` record before creating the animal. This reinforced the importance of checking generated code against the actual schema rather than relying on assumed field types.

### 2. Demo seed was not actually idempotent

The initial demo seed appeared idempotent but failed on its second execution for animals that had been marked deceased.

The generated logic checked only whether an animal had a **current** cage assignment. Deceased animals had historical assignments but no current assignment, so the second seed attempted to create another overlapping assignment and PostgreSQL correctly rejected it.

I traced the exclusion-constraint failure and changed the seed to check for any existing assignment history before creating the initial assignment.

### 3. GitHub authentication terminology

AI suggestions initially risked treating GitHub user authentication as OIDC because the assignment requested an OIDC demonstration.

After checking the actual authentication mechanism, I documented it accurately: GitHub's normal web user-login flow is OAuth 2.0, while GitHub separately provides OIDC for GitHub Actions. I chose not to label an OAuth implementation as OIDC simply to match the assignment wording.

## What I manually verified

I manually exercised the major application workflows, including:

* GitHub login/logout and session persistence
* role-based authorization
* cage and animal location display
* animal moves and location history
* cage moves and location history
* PostgreSQL conflict constraints
* husbandry event creation
* audit history
* undoing animal and cage moves
* cage ownership and temporary coverage
* CSV preview and partial validation
* CSV commit and duplicate-file protection
* whole-import undo and its safety checks
* census CSV export
* printable cage cards and QR navigation
* deterministic demo-data seeding and repeated seed execution
* production frontend/backend communication
* CSRF-protected production writes
* mobile Safari authentication and navigation

I also reviewed generated code against the Django models and database constraints rather than assuming generated interfaces or field names were correct.

AI accelerated implementation and helped surface design alternatives, but the final architecture, tradeoffs, debugging decisions, and submitted code were reviewed and tested by me.

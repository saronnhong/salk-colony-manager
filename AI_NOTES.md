# AI Notes

AI tools were used as development assistants throughout this project. I primarily used **Claude/Claude Code** and **ChatGPT** for architecture discussion, implementation assistance, debugging, and code review.

## How I used AI

**Claude / Claude Code** was used for code generation and multi-file implementation work, as well as reviewing the temporal data model, API design, database constraints, and authorization approach.

**ChatGPT** was used throughout development for incremental implementation planning, architecture review, debugging, deployment troubleshooting, testing strategy, and reviewing tradeoffs as the application evolved.

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

I manually tested the major end-to-end workflows, including authentication and authorization, animal and cage moves, temporal location history, husbandry events, audit/undo behavior, coverage assignments, CSV import/export, import undo safety, QR cage cards, and repeated demo-data seeding.

I also tested the deployed application on desktop and mobile Safari, including authenticated API requests and CSRF-protected writes.

Generated code was reviewed against the Django models, database constraints, and actual application behavior rather than assuming generated interfaces or field names were correct.

AI accelerated development and helped surface design alternatives, but the final architecture, tradeoffs, debugging decisions, and submitted code were reviewed and tested by me.

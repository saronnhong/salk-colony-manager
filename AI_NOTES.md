# AI Notes

AI tools were used throughout this project as development assistants. I used them to discuss architecture and data-model tradeoffs, generate implementation starting points, review code, troubleshoot errors, and identify edge cases. All generated code was reviewed and tested before being included.

## Tools Used

* **Claude / Claude Code** — architecture discussions, data-model review, multi-file implementation planning, and code review.
* **GitHub Copilot** — inline code completion, repetitive implementation work, and boilerplate.
* **ChatGPT** — architecture discussion, implementation guidance, debugging, test planning, and documentation.

I generally used AI for larger design discussions before implementation, then used inline assistance while coding and manually tested the resulting workflows.

## Examples Where AI Was Wrong or Incomplete

**1. Assumptions about the existing Django models**

AI occasionally generated code based on assumed field names or types that did not match the actual models. For example, import logic initially treated `Animal.strain` like a string even though it is a foreign key to `Strain`. I corrected the implementation to resolve and assign the actual `Strain` instance and verified the importer against PostgreSQL.

**2. Missing dependencies between generated changes**

While adding cage responsibility/coverage, generated code referenced `CageResponsibilityAssignmentSerializer` and `assign_cage_responsibility` from the view before the corresponding imports were present. Django exposed these as `NameError` exceptions during testing. I traced the errors, corrected the imports, and retested the complete Angular → REST API → PostgreSQL workflow.

**3. GitHub OAuth vs. OIDC**

The assignment's authentication wording led to discussion of GitHub and OIDC. Standard GitHub end-user login is an OAuth flow and should not simply be described as GitHub OIDC. I kept the implementation and documentation explicit about this distinction rather than presenting the authentication mechanism as something it is not.

## What I Verified

I manually exercised the major application workflows, including:

* GitHub authentication and role-based authorization
* animal and cage moves and location history
* husbandry recording and corrections
* cage ownership and temporary coverage
* audit history and supported undo operations
* CSV import preview, validation, partial commit, duplicate-file protection, and whole-import undo
* active-animal census CSV export
* QR cage records and printable cage cards
* deterministic demo-data generation and rerunning the seed without duplicating the colony

I also reviewed database constraints and transaction boundaries for operations where concurrent or partial writes could create invalid colony state.

AI output was treated as a starting point rather than a source of truth; implementation decisions were checked against the actual application models, database behavior, assignment requirements, and observed runtime results.

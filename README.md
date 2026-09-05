# Salk Colony Manager

A full-stack animal colony management application built for the Salk Institute AIRC Research Software Engineer take-home exercise.

The application is designed to help research teams answer a deceptively difficult question reliably:

**Where is every animal right now, how did it get there, and who is responsible for it?**

It provides temporal animal and cage tracking, husbandry records, cage ownership and coverage, printable QR cage cards, spreadsheet ingestion, census export, role-based authorization, and auditable/reversible operational workflows.

> **Demo video:** Coming soon
> **Live application:** Coming soon

---

## Overview

Animal colony data changes constantly. Animals move between cages, cages move between rack positions, racks may move between rooms, husbandry events are recorded after the fact, and responsibility changes when researchers are unavailable.

Salk Colony Manager models those changes as historical records rather than overwriting the current state.

The core location hierarchy is:

```text
Animal
  ↓
AnimalCageAssignment
  ↓
Cage
  ↓
CageRackPositionAssignment
  ↓
RackPosition
  ↓
Rack
  ↓
RackRoomAssignment
  ↓
Room
```

Current state is derived from these temporal records, allowing the application to preserve history while still answering common operational questions quickly.

---

## Intended Users

The application supports several common colony-management roles:

* Principal Investigators
* Lab Managers
* Researchers
* Students
* Facility Veterinarians

Authorization is enforced on mutation endpoints rather than relying only on the frontend.

The current role matrix allows:

| Role                   | Husbandry | Move animals/cages | Undo operations |
| ---------------------- | --------: | -----------------: | --------------: |
| Principal Investigator |       Yes |                Yes |             Yes |
| Lab Manager            |       Yes |                Yes |             Yes |
| Researcher             |       Yes |                Yes |              No |
| Student                |       Yes |                 No |              No |
| Facility Veterinarian  |       Yes |                 No |              No |

Room-scoped roles are represented in the data model but are not yet enforced by the authorization layer.

---

## Technology

### Frontend

* Angular
* TypeScript
* Angular reactive forms
* QR code generation
* Responsive HTML/CSS

### Backend

* Python
* Django
* Django REST Framework
* django-allauth

### Database

* PostgreSQL
* PostgreSQL exclusion constraints
* SQL views for derived current state

### Authentication

* GitHub social authentication
* Django sessions
* CSRF protection
* Role-based authorization

---

## Core Features

### Animal Location Tracking

Animals are assigned to cages using temporal `AnimalCageAssignment` records.

Moving an animal:

1. closes its previous assignment,
2. creates a new assignment,
3. records the person performing the operation,
4. creates a transfer husbandry event,
5. records audit information for the operation.

An animal's current cage is therefore derived from its assignment history rather than stored as a mutable `current_cage` field.

---

## Cage and Rack Location Tracking

Cages are assigned to physical rack positions through `CageRackPositionAssignment`.

Racks are similarly assigned to rooms through `RackRoomAssignment`.

This keeps **identity separate from location**. Moving a cage or rack does not change its identity, and previous locations remain available historically.

PostgreSQL exclusion constraints prevent invalid states such as:

* one animal being in two cages simultaneously,
* one cage being in two rack positions simultaneously,
* two cages occupying the same rack position simultaneously,
* one rack being assigned to two rooms simultaneously.

---

## Time and Historical State

Temporal assignments contain:

```text
valid_from
valid_to
system_from
system_to
```

`valid_from` and `valid_to` describe when something was true in the real world.

`system_from` and `system_to` describe when the database considered that record authoritative.

This separation provides a foundation for correcting late or out-of-order information without treating the time something happened as the same as the time it was entered.

Current-state SQL views include:

* `AnimalCurrentLocation`
* `CageCurrentLocation`
* `RackCurrentRoom`

---

## Husbandry

Users with appropriate permissions can record husbandry events including:

* Intake
* Cage changes
* Health checks
* Weight
* Treatment
* Death
* Transfer
* Weaning
* Tail snip

Structured event details are stored separately where appropriate, such as weight and treatment data.

The interface provides quick access to recent events, including Today, Yesterday, and All views.

Corrections can reference the original husbandry event rather than silently replacing historical information.

Death records retire the animal and close its current cage assignment, separating a biological disposition from an accidental deletion.

---

## Cage Ownership and Coverage

Cages can have a primary responsible user as well as temporary coverage.

Coverage records contain:

* responsible user,
* start time,
* optional end time,
* assigning user,
* notes.

This supports workflows such as vacation or on-call handoffs while preserving responsibility history.

Current responsibility and coverage are displayed directly on the cage record and printable cage card.

---

## QR Cage Cards

Each cage has a printable cage card containing:

* cage identifier,
* cage type,
* current location,
* current animals,
* primary responsible user,
* current coverage,
* QR code.

The QR code points to the cage's application URL.

Scanning a physical cage card therefore provides a direct path to the current digital cage record instead of encoding potentially stale animal/location information directly into the QR code.

Printed cards are formatted separately from the normal application interface, and generated PDFs default to a cage-specific filename such as:

```text
Cage-D001.pdf
```

---

## Audit Trail and Undo

Important multi-record operations are grouped under an `AuditOperation`.

Individual database changes are captured as `AuditLog` entries containing:

```text
operation
table_name
row_id
action
old_values
new_values
```

Undo is implemented as a **compensating operation**, rather than deleting history or pretending the original action never occurred.

Animal and cage moves can therefore be reversed while preserving both the original action and the reversal.

The Recent Actions interface exposes operations that remain safe to undo.

Undo is intentionally state-aware. An operation is not offered as reversible when subsequent changes would make that reversal unsafe.

---

## Spreadsheet Import

Animal records can be imported from CSV.

Expected columns currently include:

```text
local_id
sex
date_of_birth
species
strain
cage_code
```

The workflow separates validation from database mutation.

### Preview

Uploading a file first creates an import preview.

Each row is validated independently and classified as valid or invalid. Validation includes:

* required values,
* supported sex values,
* date formatting,
* known strains,
* active cage identifiers.

No animals are created during preview.

### Commit

The user can explicitly import valid rows after reviewing the preview.

Invalid rows are skipped rather than causing valid rows to be discarded.

All successfully imported records are grouped under one audit operation.

### Idempotency

A SHA-256 hash of the source file is stored with each import batch.

Previously committed files cannot simply be committed again and silently duplicate the same import.

### Whole-Import Undo

An import can be reversed as one operation.

Undo derives the records belonging to the import from the audit trail rather than trusting convenience fields on the import rows.

The application refuses an unsafe import reversal when an imported animal has subsequently been modified, moved, or received husbandry records.

This protects newer colony information from being destroyed by an old undo operation.

### Current Import Limitation

The current importer expects a known set of column names. An interactive arbitrary-column mapping interface was intentionally left out of the initial implementation.

---

## Export

The application can export the active animal census as CSV.

The census contains:

```text
animal_id
local_id
sex
date_of_birth
species
strain
cage_code
rack
position
room
```

Retired/deceased animals are excluded from the active census.

XLSX and dedicated per-diem reporting are not currently implemented.

---

## Authentication

GitHub authentication is implemented using `django-allauth`.

The browser authenticates with the Django backend and subsequent API requests use the authenticated Django session.

Mutation requests are also protected by CSRF validation.

### GitHub OAuth and OIDC

GitHub's standard end-user social login flow is OAuth-based. It should not be confused with GitHub Actions' OIDC support for authenticating CI/CD workloads to cloud providers.

The current application demonstrates GitHub user authentication through the GitHub OAuth flow.

A production deployment could separately use GitHub Actions OIDC for short-lived cloud deployment credentials rather than storing long-lived cloud credentials in GitHub.

---

## Demo Data

The project includes a deterministic demo-data management command.

The generated colony contains approximately:

* 2 rooms
* 6 racks
* 120 rack positions
* 90 demo cages
* 360 demo animals
* multiple strains
* cage ownership assignments
* temporary vacation coverage
* recent weights
* health checks
* treatments
* deceased/retired animals
* historical animal cage assignments
* historical cage locations

Demo animals use deterministic UUIDs so rerunning the seed command does not create duplicate animals.

The seed also avoids resetting current locations for animals or cages that have subsequently been moved through the application.

Run:

```bash
python manage.py seed_demo
```

The command is designed to be safely rerunnable.

---

## Local Development

### Requirements

Install:

* Python 3
* Node.js / npm
* PostgreSQL
* Git

Clone the repository and configure the backend and frontend separately.

---

## Backend Setup

From the backend directory:

```bash
cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

Create a PostgreSQL database and configure the required environment variables.

Example:

```text
POSTGRES_DB=colony_manager
POSTGRES_USER=your_database_user
POSTGRES_PASSWORD=your_database_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=your-secret-key

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

Run migrations:

```bash
python manage.py migrate
```

Optionally create an administrator:

```bash
python manage.py createsuperuser
```

Seed demo data:

```bash
python manage.py seed_demo
```

Start Django:

```bash
python manage.py runserver
```

The development API runs at:

```text
http://localhost:8000
```

---

## Frontend Setup

From the frontend directory:

```bash
cd frontend

npm install

ng serve
```

The Angular development application runs at:

```text
http://localhost:4200
```

Use `localhost` consistently during local authentication rather than mixing `localhost` and `127.0.0.1`, because session and CSRF cookies are host-specific.

---

## GitHub Authentication Setup

Create a GitHub OAuth application for local development.

Configure the callback URL as:

```text
http://localhost:8000/accounts/github/login/callback/
```

Configure the corresponding client ID and client secret as backend environment variables.

Do not commit the GitHub client secret to source control.

Production deployments require a separate callback URL corresponding to the deployed backend domain.

---

## Data Integrity

The application intentionally relies on database constraints in addition to application-level validation.

Examples include:

* foreign-key relationships,
* valid temporal range checks,
* partial unique constraints,
* PostgreSQL exclusion constraints.

Application services use database transactions and row locking for operations such as moves.

This provides a final database-level defense against concurrency errors even when two requests attempt incompatible changes at nearly the same time.

---

## Local Identifiers

Animal identifiers such as ear tags or other lab-specific identifiers are modeled separately from the animal's primary key.

Local identifiers are therefore **not assumed to be globally unique, permanent, or correct**.

Animals use UUID primary keys internally.

This allows local identifiers to be changed, reused, retired, or corrected without changing the identity of the underlying animal record.

---

## Offline and Patchy Connectivity

Animal facilities may have unreliable Wi-Fi.

The current application requires connectivity for mutations such as:

* animal moves,
* cage moves,
* husbandry records,
* responsibility changes.

This is intentional.

Allowing independent offline writes to physical-location state introduces conflict scenarios where two devices could both believe an animal or cage occupies a different location.

A future offline implementation would cache read-only cage and animal records in IndexedDB and clearly label cached information:

```text
Offline — showing cached data
```

Writes would either remain connectivity-dependent or require an explicit synchronization/conflict-resolution protocol.

Full offline mutation support was intentionally excluded from the initial implementation.

---

## Backup and Restore

PostgreSQL provides the authoritative persistent datastore.

A local database can be backed up using:

```bash
pg_dump -Fc colony_manager > colony_manager.dump
```

Restore into an empty database using:

```bash
pg_restore \
  --clean \
  --if-exists \
  --dbname=colony_manager \
  colony_manager.dump
```

Production deployments should use automated encrypted backups stored separately from the application host and periodically test restoration rather than treating successful backup creation as proof that recovery works.

A production backup/restore demonstration is still pending.

---

## Security and Data Leaving the Machine

The application sends authentication requests to GitHub when GitHub login is used.

Colony data is otherwise stored in the configured PostgreSQL database and served through the Django API.

No colony data is intentionally sent to an external AI service during normal application operation.

Secrets such as:

* Django secret keys,
* database passwords,
* GitHub OAuth client secrets,

must be supplied through environment variables and must not be committed to the repository.

---

## Accessibility

The application is designed around standard semantic HTML controls and labeled form fields.

The final accessibility review includes:

* keyboard navigation,
* visible focus state,
* sufficient contrast,
* form labels,
* status messages that do not rely exclusively on color,
* usable layouts at 200% browser zoom,
* sufficiently large mobile action targets.

A final accessibility and physical-device QA pass is still pending.

---

## Known Limitations

The current implementation intentionally prioritizes colony location integrity and common husbandry workflows over breadth.

Known limitations include:

* CSV import expects predefined columns rather than arbitrary column mapping.
* XLSX import/export is not currently implemented.
* Dedicated per-diem reporting is not currently implemented.
* Room-scoped authorization exists in the data model but is not yet enforced.
* Full offline mutation/synchronization is not implemented.
* Breeding and pedigree workflows are not fully surfaced in the UI.
* Protocol-limit alerts are not implemented.
* OCR cage-card ingestion is not implemented.
* Some undo functionality is limited to explicitly supported operational workflows.
* Production deployment and final mobile/accessibility verification are pending.

These limitations were preferred over implementing broader features at the expense of the integrity of animal location, history, authorization, and audit workflows.

---

## Design Priorities

The implementation follows several principles:

1. **Identity is not location.**
   Animals, cages, racks, and rooms retain stable identities when they move.

2. **Time is first-class data.**
   Changes create historical intervals rather than overwriting previous truth.

3. **Local identifiers are not primary keys.**
   Human-entered identifiers can be wrong, reused, or changed.

4. **The database protects important invariants.**
   Critical physical-location constraints are not enforced only by frontend logic.

5. **Undo creates history rather than deleting it.**
   Reversals are compensating operations.

6. **Potentially dangerous offline writes are not hidden behind optimistic UX.**
   Location conflicts require an explicit synchronization strategy.

7. **Common physical workflows should be fast.**
   Cage records are accessible by QR code and common actions are designed for quick mobile use.

---

## Future Work

With additional development time, priorities would include:

* read-only IndexedDB caching for patchy connectivity,
* interactive spreadsheet column mapping,
* XLSX and per-diem exports,
* richer breeding/litter workflows,
* stronger room-scoped authorization,
* protocol and capacity alerts,
* expanded automated test coverage,
* production backup automation,
* additional mobile workflow optimization.

---

## AI-Assisted Development

AI tools were used during development for architecture discussion, implementation assistance, debugging, and code review.

AI-generated suggestions were treated as proposals rather than authoritative output. Generated code was reviewed against the existing data model and tested before inclusion.

See [`AI_NOTES.md`](AI_NOTES.md) for details about the tools used, examples of incorrect or incomplete AI suggestions, and the verification process.

---

## License

See [`LICENSE`](LICENSE).

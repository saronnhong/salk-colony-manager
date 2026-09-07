# Animal Colony Manager

**Live application:** https://colony.saronnhong.com

**Demo video:** `<ADD VIDEO LINK>`

A full-stack animal colony management application built for the Salk Institute AIRC Research Software Engineer take-home assignment.

The application is designed for research labs that need to track animals, cages, physical locations, husbandry activity, and personnel responsibilities while preserving a clear history of changes.

## Features

### Colony Location Tracking

The application models physical location separately from identity:

**Animal → Cage → Rack Position → Rack → Room**

Animals, cages, and racks can move without replacing their underlying records. Location changes are stored as time-based assignments so previous locations remain available after a move.

Current location is derived from assignment history rather than stored as a mutable location field.

Database constraints prevent conflicting current assignments, including:

* an animal occupying multiple cages at the same time
* a cage occupying multiple rack positions at the same time
* multiple cages occupying the same rack position at the same time
* a rack occupying multiple rooms at the same time

### Animal and Cage History

Animal and cage detail pages display current location information and location history.

Moves are recorded as first-class operations containing information about who performed the action, when it occurred, and why.

### Husbandry Events

Users can record husbandry events including:

* health checks
* weights
* treatments
* cage changes
* transfers
* deaths

Husbandry records preserve both event time and recorded time, allowing late-entered events to retain their actual occurrence date.

### Ownership and Vacation Coverage

Cages can have a primary responsible user as well as temporary coverage assignments.

Coverage includes a validity period, allowing another lab member to cover cages during vacations or other absences without replacing the underlying primary ownership history.

### Audit History and Undo

Important colony operations create audit records identifying:

* the user who performed the operation
* when it was performed
* the type of operation
* the affected records
* old and new values where applicable

Animal and cage moves can be undone through compensating operations. Undo does not erase the original action; both the original operation and its reversal remain in the audit history.

### Spreadsheet Import

CSV animal imports use a two-stage workflow:

1. **Preview and validate**
2. **Commit valid rows**

Previewing a file does not create animal records.

The importer validates required columns and row data before commit. Invalid rows are displayed to the user and can be skipped while valid rows are imported.

Required CSV columns are:

```text
local_id,sex,date_of_birth,species,strain,cage_code
```

The raw file is SHA-256 hashed to prevent the same committed file from being accidentally imported twice.

Imports are represented as batches, allowing the entire import to be undone as a single operation.

**Undo Import** removes records created by that batch only when doing so is safe. The backend refuses the undo if imported animals have gained later husbandry events, location history, identifiers, or other state that would make deleting the import destructive.

The import batch and audit history remain after undo, providing traceability rather than silently erasing the operation.

### Census Export

The active colony census can be exported as CSV with animal identifiers, demographics, strain, and current cage/rack/room location. Retired or deceased animals are excluded.

### QR Cage Cards

Each cage has a printable cage card containing a QR code.

Scanning the QR code opens the cage directly in the web application, providing a fast path from a physical cage to its digital record.

Cards can also be printed or saved as PDF for placement on physical cages.

## Authentication and Authorization

Authentication is demonstrated using GitHub OAuth 2.0. GitHub's standard user-login flow is OAuth rather than OIDC; GitHub's OIDC support applies separately to GitHub Actions.

Authorization is handled independently from authentication.

Application roles include:

* Principal Investigator
* Lab Manager
* Researcher
* Student
* Veterinarian

Permissions determine who can manage colony locations, record husbandry events, and undo operations.

For the hosted demonstration, newly authenticated GitHub users are automatically assigned the **Lab Manager** role so reviewers can exercise the complete workflow without manual account provisioning.

A production deployment would instead use controlled role provisioning tied to institutional identity and authorization policies.

## Data Model

The database is normalized around stable entity identities and temporal assignment records. Animals, cages, racks, positions, and rooms are separate entities, while assignment tables preserve how their relationships change over time.

### Local Identifiers

Local animal identifiers are deliberately not primary keys.

Identifiers such as ear tags may be entered incorrectly, reused, or meaningful only within a particular laboratory workflow. Animals therefore use stable UUID primary keys while local identifiers are modeled separately.

### Time and Current State

Temporal assignment records use validity intervals to represent when a location was true in the real world.

Location assignment models also include system-time fields to support the distinction between real-world history and when information was represented in the database.

Current-state database views derive current animal, cage, and rack locations from this history.

PostgreSQL exclusion constraints provide a database-level integrity backstop against overlapping assignments.

## Technology

### Frontend

* Angular
* TypeScript
* Angular Material

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* GitHub OAuth

### Deployment

* Amazon S3 and CloudFront
* AWS Lightsail

## Demo Data

The included `seed_demo` management command creates a deterministic colony of approximately 360 animals across 90 cages and six racks, including multiple strains, location history, husbandry events, deaths, cage ownership, and temporary coverage.

The command is idempotent and can be safely run repeatedly.

```bash
python manage.py seed_demo
```

## Running Locally

### Clone Repository

```bash 
git clone https://github.com/saronnhong/salk-colony-manager.git salk-colony-manager
cd salk-colony-manager
```

### Backend

Create and activate a virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local PostgreSQL database:

```bash
createdb colony_manager
```

Configure the required environment variables in `backend/.env`.

Example development configuration:

```text
DEBUG=False
IS_PRODUCTION=False
FRONTEND_URL=http://localhost:4200
ALLOWED_HOSTS=localhost,127.0.0.1,52.88.174.187,api.saronnhong.com
GITHUB_CLIENT_ID=<github-oauth-client-id>
GITHUB_CLIENT_SECRET=<github-oauth-client-secret>
DJANGO_SECRET_KEY=<development-secret>
DB_NAME=colony_manager
DB_USER=<database-user>
DB_PASSWORD=<database-password>
DB_HOST=localhost
DB_PORT=5432
```

Database credentials are also supplied through environment variables and are not committed to the repository.

Run migrations:

```bash
python manage.py migrate
```

Optionally load the demo colony:

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

### Frontend

From the frontend directory:

```bash
cd frontend
npm install
ng serve
```

The development application runs at:

```text
http://localhost:4200
```

The development frontend environment points API requests to the local Django server.

## GitHub Authentication Setup

Create a GitHub OAuth application and use the following development callback URL:

`http://localhost:8000/accounts/github/login/callback/`

Set the client ID and secret in backend/.env. OAuth credentials and application secrets are not committed to source control.

## Backup and Restore

The PostgreSQL database can be backed up using `pg_dump` and restored using `pg_restore`.

Example:

```bash
pg_dump \
  -Fc \
  -d colony_manager \
  -f colony_manager.dump
```

A backup can be restored into a clean PostgreSQL database using `pg_restore`:

```bash
createdb colony_manager_restore

pg_restore \
  -d colony_manager_restore \
  colony_manager.dump
```

Production backups should be automated, stored separately from the application host, and periodically restore-tested.

## Accessibility

The interface uses semantic HTML, explicit form labels, keyboard-accessible controls, visible status/error messaging, and text in addition to visual status indicators.

The application is designed to remain usable at increased browser zoom and with responsive/mobile layouts.

## Known Limitations and Future Work

This time-boxed implementation focuses on the core colony-management workflow. Potential future work includes:

* **Offline support:** writes currently require connectivity to avoid conflicting animal or cage locations. Future work could add read-only caching and conflict-aware synchronization.
* **Institutional authentication:** replace demo GitHub authentication and automatic role assignment with institutional SSO and administrator-managed permissions.
* **Advanced colony management:** expand support for breeding, litters, pedigrees, genotypes, protocol limits, and automated alerts.

## AI-Assisted Development

AI tools were used during development for architecture discussion, code review, debugging, and implementation assistance.

All generated code was reviewed and tested before inclusion. Specific examples of useful and incorrect AI suggestions, along with verification performed during development, are documented in [`AI_NOTES.md`](AI_NOTES.md).

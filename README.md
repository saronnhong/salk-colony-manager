# Animal Colony Manager

**Live application:** https://colony.saronnhong.com
**API:** https://api.saronnhong.com
**Demo video:** `<ADD VIDEO LINK>`

A full-stack animal colony management application built for the Salk Institute AIRC Research Software Engineer take-home assignment.

The application is designed for research labs that need to track animals, cages, physical locations, husbandry activity, and personnel responsibilities while preserving a clear history of changes.

## Features

### Colony location tracking

The application models physical location separately from identity:

**Animal → Cage → Rack Position → Rack → Room**

Animals, cages, and racks can move without replacing their underlying records. Location changes are stored as time-based assignments so previous locations remain available after a move.

Current location is derived from assignment history rather than stored as a mutable location field.

Database constraints prevent conflicting current assignments, including:

* an animal occupying multiple cages at the same time
* a cage occupying multiple rack positions at the same time
* multiple cages occupying the same rack position at the same time
* a rack occupying multiple rooms at the same time

### Animal and cage history

Animal and cage detail pages display current location information and location history.

Moves are recorded as first-class operations containing information about who performed the action, when it occurred, and why.

### Husbandry events

Users can record husbandry events including:

* health checks
* weights
* treatments
* cage changes
* transfers
* deaths
* weaning
* tail snips

The application distinguishes the time an event occurred from the time it was recorded. This allows users to enter events later while preserving the actual event date.

Husbandry events also support corrections so historical information does not have to be silently overwritten.

### Ownership and vacation coverage

Cages can have a primary responsible user as well as temporary coverage assignments.

Coverage includes a validity period, allowing another lab member to cover cages during vacations or other absences without replacing the underlying primary ownership history.

### Audit history and undo

Important colony operations create audit records identifying:

* the user who performed the operation
* when it was performed
* the type of operation
* the affected records
* old and new values where applicable

Animal and cage moves can be undone through compensating operations. Undo does not erase the original action; both the original operation and its reversal remain in the audit history.

### Spreadsheet import

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

### Census export

The colony can be exported as CSV with current animal and location information, including:

* animal ID
* local identifier
* sex
* date of birth
* species
* strain
* cage
* rack
* rack position
* room

Retired/deceased animals are excluded from the active census.

### QR cage cards

Each cage has a printable cage card containing a QR code.

Scanning the QR code opens the cage directly in the web application, providing a fast path from a physical cage to its digital record.

Cards can also be printed or saved as PDF for placement on physical cages.

### Mobile workflow

The application uses responsive layouts and large interaction targets for common colony workflows.

The hosted application has been tested with mobile Safari, including GitHub authentication and QR-code navigation.

The interface is intended to keep common tasks such as opening a cage, recording husbandry information, and reviewing location information short and direct.

## Authentication and authorization

The application demonstrates authentication using GitHub.

GitHub's standard web user authentication flow is OAuth 2.0 rather than a general-purpose OpenID Connect user-login implementation. GitHub does separately support OIDC for GitHub Actions. This distinction is documented rather than describing GitHub OAuth as OIDC.

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

## Data model

The database is normalized around stable entity identities and temporal assignment records.

Important entities include:

* `Animal`
* `AnimalLocalIdentifier`
* `Cage`
* `Rack`
* `RackPosition`
* `Room`
* `AnimalCageAssignment`
* `CageRackPositionAssignment`
* `RackRoomAssignment`
* `HusbandryEvent`
* `CageResponsibility`
* `AuditOperation`
* `AuditLog`
* `ImportBatch`
* `ImportRow`

### Local identifiers

Local animal identifiers are deliberately not primary keys.

Identifiers such as ear tags may be entered incorrectly, reused, or meaningful only within a particular laboratory workflow. Animals therefore use stable UUID primary keys while local identifiers are modeled separately.

### Time and current state

Temporal assignment records use validity intervals to represent when a location was true in the real world.

Location assignment models also include system-time fields to support the distinction between real-world history and when information was represented in the database.

Current-state database views derive current animal, cage, and rack locations from this history.

PostgreSQL exclusion constraints provide a database-level integrity backstop against overlapping assignments.

## Technology

### Frontend

* Angular
* TypeScript
* Angular Material
* Angular signals
* PWA/service worker support

### Backend

* Python
* Django
* Django REST Framework
* django-allauth
* PostgreSQL
* Gunicorn
* Nginx

### Hosting

Frontend:

* Amazon S3
* Amazon CloudFront
* HTTPS
* `colony.saronnhong.com`

Backend:

* AWS Lightsail
* Ubuntu
* PostgreSQL
* Gunicorn
* Nginx
* HTTPS
* `api.saronnhong.com`

## Demo data

The application includes a deterministic demo-data management command that creates a realistic colony containing approximately 360 animals distributed across:

* multiple rooms
* six racks
* approximately 90 cages
* multiple mouse strains
* primary cage responsibilities
* temporary vacation coverage
* animal movement history
* cage movement history
* weights
* health checks
* treatments
* deaths/retired animals

The seed command is designed to be idempotent and can be run repeatedly without recreating the colony.

Run it with:

```bash
python manage.py seed_demo
```

## Running locally

### Backend

Create and activate a virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a PostgreSQL database and configure the required environment variables in `backend/.env`.

Example development configuration:

```text
DEBUG=True
IS_PRODUCTION=False
FRONTEND_URL=http://localhost:4200
ALLOWED_HOSTS=localhost,127.0.0.1
GITHUB_CLIENT_ID=<github-oauth-client-id>
GITHUB_CLIENT_SECRET=<github-oauth-client-secret>
DJANGO_SECRET_KEY=<development-secret>
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

## GitHub authentication setup

A GitHub OAuth application is required for local authentication.

Development callback URL:

```text
http://localhost:8000/accounts/github/login/callback/
```

The hosted deployment uses a separate OAuth application because GitHub OAuth applications support a configured callback URL.

Production callback:

```text
https://api.saronnhong.com/accounts/github/login/callback/
```

OAuth client secrets and Django secrets are supplied through environment variables and are not stored in source control.

## Offline and unreliable network design

The application is installable as an Angular PWA and uses a service worker for application assets.

Full offline mutation/synchronization was intentionally not implemented.

Animal moves, cage moves, husbandry events, and other writes have integrity and ordering consequences. Queuing these writes independently on multiple offline devices could create conflicts such as two users assigning the same cage or animal to different locations.

A production extension would cache read-only cage and animal information locally while clearly indicating that the information may be stale. Mutating operations would require connectivity unless a dedicated synchronization/conflict-resolution protocol were introduced.

The application therefore does not silently claim successful colony writes while offline.

## Backup and restore

The PostgreSQL database is designed to be backed up using `pg_dump`.

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

Production database credentials should be supplied through environment variables or PostgreSQL configuration rather than embedded in backup scripts.

For a production research system, backups should be automated, encrypted, stored separately from the application host, and periodically restore-tested.

## Security

The deployed application uses HTTPS for both frontend and API traffic.

Production configuration includes:

* Django `DEBUG=False`
* secure session and CSRF cookies
* explicit CORS origins
* explicit CSRF trusted origins
* credentialed API requests
* CSRF protection on mutating requests
* PostgreSQL not exposed publicly
* secrets stored outside source control
* role-based authorization for colony operations

No application secrets are intentionally committed to the repository.

## Accessibility

The interface uses semantic HTML, explicit form labels, keyboard-accessible controls, visible status/error messaging, and text in addition to visual status indicators.

The application is designed to remain usable at increased browser zoom and with responsive/mobile layouts.

## Known limitations and future work

Given the time-boxed nature of the assignment, several production features were intentionally scoped out.

Potential extensions include:

* read-only IndexedDB caching for unreliable network conditions
* robust offline synchronization and conflict resolution
* institutional OIDC/SSO integration
* administrator-managed role provisioning
* protocol and colony-size limits
* genotype tracking
* pedigree and breeding visualization
* litter-management workflows
* automated alerts and reminders
* OCR-assisted cage-card ingestion
* more comprehensive reporting and per-diem exports
* automated database backup scheduling
* broader automated test coverage

The focus of this implementation is the core colony workflow: reliable identity and location tracking, temporal history, husbandry records, ownership and coverage, auditability, reversible operations, spreadsheet ingestion, and practical mobile access.

## AI-assisted development

AI tools were used during development for architecture discussion, code review, debugging, and implementation assistance.

All generated code was reviewed and tested before inclusion. Specific examples of useful and incorrect AI suggestions, along with verification performed during development, are documented in [`AI_NOTES.md`](AI_NOTES.md).

## License

See [`LICENSE`](LICENSE).

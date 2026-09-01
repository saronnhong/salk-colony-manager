# Animal Colony Manager

A mobile-first animal colony management application for tracking research animals, cages, and physical locations within a vivarium.

The application is designed around a simple but important question:

**Where is every animal right now, and how did it get there?**

Rather than storing only an animal's current cage or a cage's current rack position, the system models movements as temporal assignments. This preserves location history and provides a foundation for auditing moves, correcting records, and handling events that may be entered after they occurred.

## Status

This project is currently under active development.

### Implemented

* Animal, cage, rack, rack-position, and room data models
* PostgreSQL-backed temporal location assignments
* Animal-to-cage assignment history
* Cage-to-rack-position assignment history
* Database constraints preventing overlapping current assignments
* Current-location database views
* Human-readable animal identifiers
* Demo colony seed data
* Django Admin support
* REST API for animals and cages
* Cage list API with current physical locations and animal counts
* Animal API with current cage information
* Mobile-first Angular cage list
* Cage detail view showing physical location and current animals
* Loading and error states in the Angular application

### In Progress / Planned

* Animal movement workflow and movement history
* Cage relocation workflow
* Husbandry event recording
* Audit history and corrections
* Authentication and role-based authorization
* Spreadsheet import with preview and validation
* CSV/XLSX export
* Import undo
* QR-based cage lookup
* Limited offline access to recently viewed records
* Coverage/on-call information
* Automated tests
* Production deployment

## Who This Is For

The application is intended for researchers and animal-care staff managing laboratory animal colonies.

The interface is designed to work well on a phone so common workflows can be performed while working in an animal facility rather than requiring users to return to a desktop computer.

Example workflows include:

* Finding the current location of an animal
* Viewing all animals currently assigned to a cage
* Moving an animal between cages
* Relocating a cage within the facility
* Reviewing an animal's location history
* Recording husbandry events
* Accessing a cage record by scanning a QR code
* Importing existing colony records from spreadsheets

## Architecture

The application uses a separated frontend, API, and relational database architecture:

```text
Angular + TypeScript
        |
        | REST API
        v
Django REST Framework
        |
        v
PostgreSQL
```

### Frontend

* Angular
* TypeScript
* SCSS
* Angular Material

The frontend is designed mobile-first, with iOS Safari as an important target.

### Backend

* Python
* Django
* Django REST Framework

Django provides the domain model, API, administrative interface, validation, and application services.

### Database

* PostgreSQL

PostgreSQL was selected in part because the application relies on database-level temporal integrity constraints.

## Data Model

The core location hierarchy is:

```text
Animal
   |
   v
AnimalCageAssignment
   |
   v
Cage
   |
   v
CageRackPositionAssignment
   |
   v
RackPosition
   |
   v
Rack
   |
   v
Room
```

An animal does not simply contain a mutable `cage_id`, and a cage does not simply contain a mutable `rack_position_id`.

Instead, location changes are represented as assignments with time intervals.

For example:

```text
M001

Aug 25 ───────── Sep 1
       CAGE-001

                  Sep 1 ───────── Present
                         CAGE-003
```

This allows the system to answer both:

**Where is M001 now?**

and:

**Where was M001 on August 30?**

## Temporal Data

Assignments contain two types of time.

### Valid Time

`valid_from` and `valid_to` represent when something was true in the real world.

For example, an animal may have physically moved at 10:00 AM.

### System Time

`system_from` and `system_to` represent when the database believed a record was current.

This distinction provides a foundation for handling late or corrected records without losing the history of what was previously recorded.

## Location Integrity

PostgreSQL exclusion constraints are used to prevent overlapping active assignments.

This protects against states such as:

```text
M001
├── CAGE-001  Aug 25 → Present
└── CAGE-003  Sep 1  → Present
```

where the same animal would incorrectly appear to be in two cages simultaneously.

Similar constraints protect cage-to-rack-position assignments.

Current-location database views provide a convenient representation of the current state while the assignment tables remain the source of truth.

## API

The Django REST Framework API currently exposes read access to animals and cages.

### List Animals

```http
GET /api/animals/
```

Returns animals including their local identifier and current cage.

Example:

```json
{
  "id": "6e3aec09-f7c7-55c9-9a12-e216b84a1787",
  "identifier": "M001",
  "sex": "M",
  "date_of_birth": "2026-06-02",
  "species": "Mus musculus",
  "strain_name": "C57BL/6J",
  "current_location": {
    "cage_id": "264f2d79-526e-457d-9ae8-6ea4448f9ddf",
    "cage_code": "CAGE-001",
    "valid_from": "2026-08-25T08:00:00Z"
  }
}
```

### List Cages

```http
GET /api/cages/
```

Returns cages with their current physical location and number of animals.

Example:

```json
{
  "id": "264f2d79-526e-457d-9ae8-6ea4448f9ddf",
  "cage_code": "CAGE-001",
  "cage_type": "standard",
  "current_location": {
    "room": "Mouse Room A",
    "rack": "RACK-A",
    "position": "A-01"
  },
  "animal_count": 2
}
```

### Cage Detail

```http
GET /api/cages/{id}/
```

Returns cage information, physical location, and the animals currently assigned to the cage.

### Cage Animals

```http
GET /api/cages/{id}/animals/
```

Returns the animals currently assigned to a cage.

## Demo Data

The project includes deterministic demo data so the application can be evaluated without manually constructing a colony.

The demo colony currently contains:

* 2 rooms
* 2 racks
* 20 rack positions
* 6 cages
* 12 animals
* C57BL/6J and BALB/cJ strains

Animals use readable identifiers:

```text
M001
M002
M003
...
M012
```

The initial cages are:

```text
CAGE-001
CAGE-002
CAGE-003
CAGE-004
CAGE-005
CAGE-006
```

Each cage initially contains two animals.

## Running Locally

### Prerequisites

Install:

* Python
* PostgreSQL
* Node.js
* npm
* Angular CLI

## Backend Setup

From the backend directory, create and activate a Python virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies.

```bash
pip install -r requirements.txt
```

Create a PostgreSQL database for the application.

Create a `.env` file in the backend directory:

```env
POSTGRES_DB=colony_manager
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Do not commit `.env` or database credentials to source control.

Apply the migrations:

```bash
python manage.py migrate
```

Optionally create a Django administrator:

```bash
python manage.py createsuperuser
```

Load the demo colony:

```bash
python manage.py seed_demo
```

Start Django:

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/api/
```

The Django Admin interface is available at:

```text
http://127.0.0.1:8000/admin/
```

## Frontend Setup

From the frontend directory:

```bash
npm install
```

Start the Angular development server:

```bash
ng serve
```

Open:

```text
http://localhost:4200
```

The frontend expects the local Django API at:

```text
http://127.0.0.1:8000/api/
```

Both servers must currently be running when developing locally.

## Development CORS

During local development, Django allows requests from the Angular development server:

```text
http://localhost:4200
```

Production deployments should restrict allowed origins to the deployed frontend.

## Data Leaving the Machine

When running the current application locally, colony data is stored in the configured PostgreSQL database and is exchanged between the local Angular frontend and Django backend.

No colony data is intentionally sent to third-party AI services by the application.

Development of this project used AI-assisted programming tools. See `AI_NOTES.md` for details about how those tools were used and how generated code was reviewed.

## Secrets and API Keys

Secrets should be supplied through environment variables and must not be committed to the repository.

The repository's `.gitignore` excludes local environment files such as:

```text
.env
```

Authentication-related secrets will also be configured through environment variables when authentication is added.

## Cost

The application can be run entirely on a local development machine at no additional cost.

Production hosting costs will depend on the deployment platform selected for the frontend, backend, and PostgreSQL database.

## Known Limitations

The project is still under development.

Current limitations include:

* Animal and cage data are currently read-only through the public application UI.
* Animal moves and cage relocations are not yet available through the frontend.
* Authentication and authorization are not yet implemented.
* Spreadsheet import/export is not yet implemented.
* QR cage lookup is not yet implemented.
* Offline support is not yet implemented.
* Husbandry workflows are not yet implemented.
* Production deployment is not yet configured.

These limitations will be updated as development progresses.

## Design Priorities

The project prioritizes:

1. **Traceability** — movements and corrections should preserve history.
2. **Data integrity** — invalid colony states should be prevented whenever practical at the database layer.
3. **Fast physical-to-digital access** — cage records should be quickly accessible from a phone.
4. **Mobile usability** — common workflows should work comfortably with one hand.
5. **Auditability** — important actions should record who performed them and when.
6. **Interoperability** — existing spreadsheet-based colony data should be importable and exportable.
7. **Recoverability** — destructive operations should favor versioning and compensating actions over permanent deletion.

## AI-Assisted Development

AI tools were used during development for architecture discussion, code generation, debugging, and review.

AI-generated suggestions were treated as implementation proposals rather than authoritative answers. Generated code was reviewed and tested before inclusion.

Examples of AI-generated recommendations that required correction included:

* Deprecated Django constraint syntax that was incompatible with the version of Django used by the project.
* An initial animal-identifier model that incorrectly tied identifier uniqueness to an animal's room even though room location changes over time.

Additional details are documented in `AI_NOTES.md`.

## License

See the repository's `LICENSE` file for licensing information.

## Demo

**Demo video:** Coming soon

A short demonstration video will be added here before submission.


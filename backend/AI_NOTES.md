AI_NOTES.md
AI Tools Used

I used Claude AI primarily as a senior-engineer-style planning and implementation assistant. I used it to explore the initial data model, reason through temporal animal/cage location history, generate an initial set of Django models and PostgreSQL migrations, and discuss API and application architecture.

I also used ChatGPT to review architectural decisions and generated code, troubleshoot Django/PostgreSQL issues, and validate the implementation against the version of Django used by the project.

I used GitHub Copilot in VS Code for inline code completion and small implementation tasks.

All AI-generated code was reviewed before being incorporated into the project. I treated generated code as a starting point rather than assuming it was correct.

Decisions and Corrections
1. Temporal location history instead of mutable location fields

The initial design discussion considered storing an animal's current cage directly on the Animal model. I decided against making this the source of truth because updating a cage_id would destroy historical location information.

Instead, the application models location as temporal assignments:

AnimalCageAssignment records when an animal occupied a cage.
CageRackPositionAssignment records when a cage occupied a rack position.

This also keeps cage identity separate from physical location. Moving a cage therefore does not require changing the location history of every animal inside it.

PostgreSQL exclusion constraints prevent an animal or rack position from having overlapping active assignments.

2. I rejected room-scoped animal identifiers

An early generated model added a room foreign key to AnimalLocalIdentifier so identifiers could be made unique within a room.

I removed this approach.

Local animal identifiers can be reused, entered incorrectly, and are not inherently tied to a room. Room is also temporal because an animal can move. Storing the current room on an identifier would duplicate information derived from the animal → cage → rack position history and would require keeping that value synchronized whenever an animal or cage moved.

Instead, identifiers remain searchable records associated with the animal, and ambiguity can be handled explicitly by the application rather than imposing an unsupported uniqueness rule.

3. Current location is derived rather than duplicated

The initial design considered caching fields such as Animal.current_cage and Cage.current_rack_position.

I decided not to maintain these duplicate fields. At the expected scale of a few hundred animals, PostgreSQL can derive current location efficiently from the temporal assignment tables.

The application therefore uses database views for current animal and cage locations while retaining the assignment tables as the source of truth.

4. Undo is a new operation, not deletion of history

For auditing, I chose to group changes under AuditOperation records with individual AuditLog entries describing affected records.

Undo does not delete the original operation. Instead, it creates a new compensating operation referencing the operation it reverses. This preserves the fact that the original action occurred and records who reversed it and when.

While implementing this, an AI-generated property accessed Django's dynamically generated reversed_by_operations relationship directly. Pylance could not infer that relationship. I replaced it with an explicit AuditOperation.objects.filter(reverses_operation=self).exists() query, which is clearer to static analysis while preserving the same behavior.

# CRM Backend — Design Notes

## Data Model

Three tables in a parent-child hierarchy:

```
Company
  └── Contact        (company_id FK, optional)
        └── Interactions   (contact_id FK, CASCADE)
              └── Note     (interaction_id FK, CASCADE)
```

**Company** — `name` (unique, indexed) and `industry`. Optional — a contact can exist without one.

**Contact** — owns `company: str` (display name, unique), `phone_number` (unique, the dedup key), `role`, `name`, and an optional `company_id` FK linking to the full Company row. The ORM relationship is named `company_details` to avoid colliding with the inherited `company: str` field.

**Interactions** — a logged event (call, meeting, email) tied to a contact. Has `title`, `description`, and an auto-set UTC `timestamp`.

**Note** — free-text annotation on an interaction. Has `text` and `created_at`.

Deletes cascade downward: removing a Contact removes all its Interactions and Notes; removing an Interactions row removes its Notes.

---

## Deduplication

`phone_number` is the single canonical key. All ingestion goes through one function — `create_or_update_contact`:

- `phone_number` **not found** → insert new Contact
- `phone_number` **found** → update existing Contact

If a contact tries to change their `phone_number` to one already owned by a *different* contact, a new record is created by merging the current fields with the requested changes. The original contact is left untouched and no error is raised.

The DB-level `UNIQUE` constraint on `phone_number` acts as a hard backstop in case anything bypasses the application layer.


`phone_number` is the single canonical key for deduplication. The logic lives in one place — `crud.create_or_update_contact` — so no caller needs to implement it themselves:

```
POST /contacts/  →  create_or_update_contact(phone_number)
                         │
                         ├── phone_number not found → INSERT new Contact
                         │
                         └── phone_number found     → UPDATE 

**Conflict handling on updates removed but can be roll back**  
If an existing contact tries to change their `phone_number` to one already registered by a *different* contact, `crud.update_contact` raises a `ValueError` before touching the database. The router catches this and returns HTTP 409 Conflict. This means:

- The caller gets a clear, actionable error rather than a silent overwrite or a raw database integrity error.
- The check happens at the application layer, so the error message is human-readable regardless of which database is behind SQLAlchemy.
- The DB-level `UNIQUE` constraint on `phone_number` is still present as a hard backstop in case anything bypasses the application layer.

---

## Assumptions

- `phone_number` is stored as `int`. This works for most numbers but cannot represent leading zeros or extensions — a `str` field would be safer for international formats.
- `company: str` on `ContactsBase` is kept as specified. The separate `Company` table is linked via `company_id` and surfaced as `company_details` in responses to avoid a field name collision.
- Passwords and hashed credentials are excluded from the Contact model entirely — authentication is assumed to be handled by a separate layer.
- Timestamps are always set server-side in UTC. No client-supplied timestamps are accepted.
- `company_id` is nullable — contacts do not require a Company row to exist first.

## Run
cd app
fastapi dev
uvicorn app.main:app --reload
Assumptions: postgres running

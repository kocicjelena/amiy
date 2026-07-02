# CRM API

A lightweight in-memory CRM built with FastAPI. No database, no authentication.

---

## How to Run

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

---

## Data Model

Three plain Pydantic models — no ORM, no tables:

```
Company
  └── Contact        (references company by name)
        └── Interaction    (list stored directly on the contact record)
```

**Company** — `name` (unique) and optional `industry`. Must be created before a contact can reference it.

**Contact** — `phone_number` (unique, the dedup key), `name`, `role`, and `company` (the company name string). Stored in a dict keyed by `phone_number`.

**Interaction** — `notes` (text) and `timestamp` (auto-set to UTC on creation). Stored as a list directly on the contact record — no separate collection needed.

All state lives in `store.py` as a single module-level object with two dicts:

```python
companies : dict[str, Company]        # keyed by name
contacts  : dict[int, _ContactRecord] # keyed by phone_number
```

Importing `store` anywhere in the process returns the same instance — no dependency injection or session management required.

---

## Deduplication

`phone_number` is the single canonical key. `POST /contacts/` is the only ingestion endpoint — it decides internally:

- `phone_number` **not found** → insert new contact
- `phone_number` **found** → update the existing record in place

No separate PUT endpoint exists. Callers never need to check for existence first.

The company name supplied on create/update must already exist in the store. If it doesn't, a `404` is returned — this prevents dangling references and makes the constraint explicit rather than silently creating a company.

---

## Assumptions

- **In-memory only** — all data is lost when the process restarts. This is intentional per requirements; swap `store.py` for a database-backed store to persist.
- **Company is a prerequisite** — contacts cannot be created without a matching company name already in the store.
- **`phone_number` as `int`** — works for most numbers but cannot represent leading zeros or extensions. Use `str` for international formats.
- **No auth** — all endpoints are public. Add an API key dependency to `main.py` if needed.
- **Timestamps are UTC, server-set** — `Interaction.timestamp` is assigned at the moment the request is processed; no client-supplied timestamps are accepted.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/companies/` | Create a company |
| `GET` | `/companies/` | List all companies |
| `GET` | `/companies/{name}` | Get one company |
| `DELETE` | `/companies/{name}` | Delete a company |
| `POST` | `/contacts/` | Create **or** update contact by phone number |
| `GET` | `/contacts/{phone}` | Contact + company info + all interactions |
| `PATCH` | `/contacts/{phone}` | Partial update |
| `DELETE` | `/contacts/{phone}` | Delete a contact |
| `POST` | `/contacts/{phone}/interactions` | Log an interaction |
| `GET` | `/contacts/{phone}/interactions` | List interactions |

crm/
├── main.py
├── models.py
├── store.py
└── routers/
    ├── companies.py
    ├── contacts.py
    └── interactions.py

pip install fastapi uvicorn
uvicorn app.main:app --reload   # run from the parent of  or 
fastapi dev

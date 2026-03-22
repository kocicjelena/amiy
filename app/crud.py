import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    Contact,
    ContactCreate,
    ContactUpdate,
    Interactions,
    InteractionsCreate,
    Note,
    NoteCreate,
)


# ──────────────────────────── Company ────────────────────────────


def create_company(*, session: Session, company_in: CompanyCreate) -> Company:
    db_obj = Company.model_validate(company_in)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_company(*, session: Session, company_id: uuid.UUID) -> Company | None:
    return session.get(Company, company_id)


def get_company_by_name(*, session: Session, name: str) -> Company | None:
    return session.exec(select(Company).where(Company.name == name)).first()


def update_company(
    *, session: Session, db_company: Company, company_in: CompanyUpdate
) -> Company:
    db_company.sqlmodel_update(company_in.model_dump(exclude_unset=True))
    session.add(db_company)
    session.commit()
    session.refresh(db_company)
    return db_company


def delete_company(*, session: Session, db_company: Company) -> None:
    session.delete(db_company)
    session.commit()


# ──────────────────────────── Contact ────────────────────────────


def create_contact(*, session: Session, contact_create: Contact) -> Contact:
    db_obj = Contact.model_validate(contact_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_contact(
    *, session: Session, db_contact: Contact, contact_in: Contact
) -> Contact:
    """Partially update a contact.

    Collision rule: if the incoming phone_number belongs to a different contact,
    create a new contact record (merging current fields + changes) instead of
    overwriting or returning 409.
    """
    contact_data = contact_in.model_dump(exclude_unset=True)

    new_phone = contact_data.get("phone_number")
    if new_phone is not None and new_phone != db_contact.phone_number:
        collision = get_contact_by_phone_number(session=session, phone_number=new_phone)
        if collision and collision.id != db_contact.id:
            merged: dict[str, Any] = db_contact.model_dump(
                exclude={"id", "company_details", "interactions"}
            )
            merged.update(contact_data)
            return create_contact(
                session=session,
                contact_create=Contact.model_validate(merged),
            )

    db_contact.sqlmodel_update(contact_data)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


def create_or_update_contact(
    *, session: Session, contact_in: Contact
) -> tuple[Contact, bool]:
    """Upsert by phone_number. Returns (contact, created)."""
    existing = get_contact_by_phone_number(
        session=session, phone_number=contact_in.phone_number
    )
    if existing:
        updated = update_contact(
            session=session,
            db_contact=existing,
            contact_in=Contact.model_validate(contact_in.model_dump()),
        )
        return updated, False
    return create_contact(session=session, contact_create=contact_in), True


def get_contact_by_phone_number(
    *, session: Session, phone_number: int
) -> Contact | None:
    return session.exec(
        select(Contact).where(Contact.phone_number == phone_number)
    ).first()


def get_contact_with_details(
    *, session: Session, contact_id: uuid.UUID
):
    """Fetch a contact with company_details and interactions (+ notes) eager-loaded.

    Uses selectinload so all three levels are fetched in separate IN-clause
    queries — no N+1, no cartesian product from joins.
    """
    return session.exec(
        select(Contact)
        .where(Contact.id == contact_id)
        # .options(
        #     selectinload(Contact.company_id),
        #     selectinload(Contact.interactions).selectinload(Interactions.notes),
        # )
    ).first()


# ──────────────────────────── Interactions ────────────────────────────


def create_interaction(
    *,
    session: Session,
    interaction_in: InteractionsCreate,
    contact_id: uuid.UUID,
) -> Interactions:
    db_obj = Interactions.model_validate(interaction_in, update={"contact_id": contact_id})
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_interaction(
    *, session: Session, interaction_id: uuid.UUID
) -> Interactions | None:
    return session.get(Interactions, interaction_id)


def get_interactions_for_contact(
    *,
    session,
    contact_id,
    skip: int = 0,
    limit: int = 100,
):
    #  total: int = session.exec(
    #     select(func.count())
    #     .select_from(Interactions)
    #     .where(Interactions.contact_id == contact_id)
    # ).one()
    rows = list(
        session.exec(
            select(Interactions)
            .where(Interactions.contact_id == contact_id)
            .offset(skip)
            .limit(limit)
        ).all()
    )
    return rows


def delete_interaction(*, session: Session, db_interaction: Interactions) -> None:
    session.delete(db_interaction)
    session.commit()


# ──────────────────────────── Note ────────────────────────────


def create_note(
    *, session: Session, note_in: NoteCreate, interaction_id: uuid.UUID
) -> Note:
    db_note = Note.model_validate(note_in, update={"interaction_id": interaction_id})
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    return db_note


def get_note(*, session: Session, note_id: uuid.UUID) -> Note | None:
    return session.get(Note, note_id)


def get_notes_for_interaction(
    *,
    session: Session,
    interaction_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
):
    
    rows = list(
        session.exec(
            select(Note)
            .where(Note.interaction_id == interaction_id)
            .offset(skip)
            .limit(limit)
        ).all()
    )
    return rows


def delete_note(*, session: Session, db_note: Note) -> None:
    session.delete(db_note)
    session.commit()


# ──────────────────────────── Deduplication ──────────────────────────────────


def find_interactions_by_phone_numbers(
    *,
    session: Session,
    query_phone_numbers: list[int],
    interaction_ids: list[uuid.UUID] | None = None,
) -> list[tuple[Interactions, int]]:
    stmt = (
        select(Interactions, Contact.phone_number)
        .where(Contact.phone_number in(query_phone_numbers))
    )
    
    if interaction_ids:
        stmt = stmt.where(Interactions.id in (interaction_ids))
    return [(row[0], int(row[1])) for row in session.exec(stmt).all()]

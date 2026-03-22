import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import select, Session

from app import crud
from app.api.deps import CurrentContact, get_current_active_supercontact
from app.core.db import get_session
from app.models import (
    Contact,
    ContactCreate,
    ContactPublic,
    ContactsPublic,
    ContactUpdate,
    ContactWithInteractions,
    Message,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])


# ──────────────────────────── List all ───────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(get_current_active_supercontact)]
)
def read_contacts(session, skip: int = 0, limit: int = 100):
    #count: int = session.exec(select(func.count(Contact.id))).one()
    contacts = list(session.exec(select(Contact).offset(skip).limit(limit)).all())
    return contacts


# ──────────────────────────── Upsert ─────────────────────────────────────────

# get_current_active_supercontact made to have 
# administrator for app
@router.post(
    "/",
    dependencies=[Depends(get_current_active_supercontact)],
 #   response_model=None,
)
def create_or_update_contact(
    *, contact_in, session: Session = Depends(get_session)):
#) -> Contact:
    contact, _ = crud.create_or_update_contact(session=session, contact_in=contact_in)
    return contact


# ──────────────────────────── Self endpoints ─────────────────────────────────


@router.get("/me", response_model=Contact)
def read_contact_me(current_contact: Contact) -> Contact:
    return current_contact


@router.patch("/me", response_model=Contact)
def update_contact_me(
    *,
    contact_in: Contact,
    current_contact: Contact,
    session: Session = Depends(get_session),
) -> Any:
    return crud.update_contact(
        session=session, db_contact=current_contact, contact_in=contact_in
    )


# ──────────────────────────── Fetch one contact (full detail) ────────────────
#
# Returns ContactWithInteractions:
#   • company (str)          — from ContactsBase
#   • company_details        — Company row (name + industry), eager-loaded
#   • interactions           — all logged events, each with their notes


@router.get("/{contact_id}", response_model=Contact)
def read_contact_by_id(
    contact_id: uuid.UUID,
    current_contact: CurrentContact,
    session: Session = Depends(get_session),
) -> Contact:
    """Return a contact with company details and full interaction history."""
    contact = crud.get_contact_with_details(session=session, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact.id != current_contact.id:
        if not getattr(current_contact, "is_supercontact", False):
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return contact


# ──────────────────────────── Delete ─────────────────────────────────────────


@router.delete(
    "/{contact_id}",
    dependencies=[Depends(get_current_active_supercontact)],
    response_model=Message,
)
def delete_contact(contact_id: uuid.UUID, session: Session = Depends(get_session)) -> Any:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    session.delete(contact)
    session.commit()
    return Message(message="Contact deleted successfully")

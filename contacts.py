from fastapi import APIRouter, HTTPException

from models import (
    Company,
    ContactCreate,
    ContactDetail,
    ContactPublic,
    ContactUpdate,
    Message,
)
from store import _ContactRecord, store

router = APIRouter(prefix="/contacts", tags=["contacts"])


# ──────────────────────────── Create or Update ───────────────────────────────
#
# Deduplication rule — phone_number is the canonical key:
#   • Not found  → create a new contact.
#   • Found      → update the existing contact's fields.
#
# Conflict handling:
#   The company name supplied in the request must already exist in the store.
#   If it doesn't, 404 is returned — create the company first.


@router.post("/", response_model=ContactPublic)
def create_or_update_contact(contact_in: ContactCreate) -> ContactPublic:
    """Create a contact or update one that already has this phone number."""
    if contact_in.company not in store.companies:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{contact_in.company}' not found. Create it first.",
        )

    existing = store.contacts.get(contact_in.phone_number)

    if existing:
        # Update — only overwrite fields that are explicitly provided
        existing.name = contact_in.name if contact_in.name is not None else existing.name
        existing.role = contact_in.role
        existing.company = contact_in.company
    else:
        # Create
        store.contacts[contact_in.phone_number] = _ContactRecord(
            name=contact_in.name,
            phone_number=contact_in.phone_number,
            role=contact_in.role,
            company=contact_in.company,
        )

    record = store.contacts[contact_in.phone_number]
    return ContactPublic(
        name=record.name,
        phone_number=record.phone_number,
        role=record.role,
        company=record.company,
    )


# ──────────────────────────── Retrieve (full detail) ─────────────────────────
#
# Returns company info (name + industry) and all interactions.


@router.get("/{phone_number}", response_model=ContactDetail)
def get_contact(phone_number: int) -> ContactDetail:
    """Return a contact with company information and all interactions."""
    record = store.contacts.get(phone_number)
    if not record:
        raise HTTPException(status_code=404, detail="Contact not found")

    company = store.companies.get(record.company)
    if not company:
        # Company was deleted after the contact was created
        company = Company(name=record.company)

    return ContactDetail(
        name=record.name,
        phone_number=record.phone_number,
        role=record.role,
        company=company,
        interactions=record.interactions,
    )


# ──────────────────────────── Patch ──────────────────────────────────────────


@router.patch("/{phone_number}", response_model=ContactPublic)
def update_contact(phone_number: int, contact_in: ContactUpdate) -> ContactPublic:
    """Partially update a contact by phone number."""
    record = store.contacts.get(phone_number)
    if not record:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact_in.company and contact_in.company not in store.companies:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{contact_in.company}' not found.",
        )

    if contact_in.name is not None:
        record.name = contact_in.name
    if contact_in.role is not None:
        record.role = contact_in.role
    if contact_in.company is not None:
        record.company = contact_in.company

    return ContactPublic(
        name=record.name,
        phone_number=record.phone_number,
        role=record.role,
        company=record.company,
    )


# ──────────────────────────── Delete ─────────────────────────────────────────


@router.delete("/{phone_number}", response_model=Message)
def delete_contact(phone_number: int) -> Message:
    if phone_number not in store.contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    del store.contacts[phone_number]
    return Message(message="Contact deleted")

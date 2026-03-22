import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentContact, Session
from app.models import (
    Contact,
    Interactions,
    InteractionsCreate,
    InteractionsList,
    InteractionsPublic,
    Note,
    NoteCreate,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])


# ──────────────────────────── Interactions ───────────────────────────────────


@router.post("/{contact_id}")
def add_interaction(
    contact_id,
    interaction_in,
    session,
    current_contact
):
    """Log a new interaction against an existing contact."""
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact.id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.create_interaction(
        session=session, interaction_in=interaction_in, contact_id=contact_id
    )


@router.get("/{contact_id}")
def list_interactions(
    contact_id,
    session,
    current_contact,
    skip: int = 0,
    limit: int = 100,
):
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact.id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    rows, total = crud.get_interactions_for_contact(
        session=session, contact_id=contact_id, skip=skip, limit=limit
    )
    #return InteractionsList(interactions=[InteractionsPublic.from_orm(row) for row in rows], count=total)
    return rows, total

@router.get("/detail/{interaction_id}")
def get_interaction(
    interaction_id,
    session,
    current_contact,
):
    interaction = crud.get_interaction(session=session, interaction_id=interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    if interaction.contact_id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return interaction


@router.delete("/detail/{interaction_id}", status_code=204)
def delete_interaction(
    interaction_id,
    session,
    current_contact,
):
    interaction = crud.get_interaction(session=session, interaction_id=interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    if interaction.contact_id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    crud.delete_interaction(session=session, db_interaction=interaction)


# ──────────────────────────── Notes ──────────────────────────────────────────


@router.post(
    "/detail/{interaction_id}/notes", status_code=201
)
def add_note(
    interaction_id,
    note_in,
    session,
    current_contact,
):
    interaction = crud.get_interaction(session=session, interaction_id=interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    if interaction.contact_id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return crud.create_note(
        session=session, note_in=note_in, interaction_id=interaction_id
    )


@router.get(
    "/detail/{interaction_id}/notes/{note_id}"
)
def get_note(
    interaction_id,
    note_id,
    session,
    current_contact,
):
    note = crud.get_note(session=session, note_id=note_id)
    if not note or note.interaction_id != interaction_id:
        raise HTTPException(status_code=404, detail="Note not found")

    interaction = crud.get_interaction(session=session, interaction_id=interaction_id)
    if interaction and interaction.contact_id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return note


@router.delete("/detail/{interaction_id}/notes/{note_id}", status_code=204)
def delete_note(
    interaction_id,
    note_id,
    session,
    current_contact,
):
    note = crud.get_note(session=session, note_id=note_id)
    if not note or note.interaction_id != interaction_id:
        raise HTTPException(status_code=404, detail="Note not found")

    interaction = crud.get_interaction(session=session, interaction_id=interaction_id)
    if interaction and interaction.contact_id != current_contact.id and not getattr(
        current_contact, "is_supercontact", False
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    crud.delete_note(session=session, db_note=note)

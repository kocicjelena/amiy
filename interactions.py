from fastapi import APIRouter, HTTPException

from models import Interaction, InteractionCreate
from store import store

router = APIRouter(prefix="/contacts", tags=["interactions"])


# ──────────────────────────── Log interaction ─────────────────────────────────


@router.post("/{phone_number}/interactions", response_model=Interaction, status_code=201)
def log_interaction(phone_number: int, interaction_in: InteractionCreate) -> Interaction:
    """Add an interaction (note + timestamp) to an existing contact."""
    record = store.contacts.get(phone_number)
    if not record:
        raise HTTPException(status_code=404, detail="Contact not found")

    interaction = Interaction(notes=interaction_in.notes)
    record.interactions.append(interaction)
    return interaction


# ──────────────────────────── List interactions ───────────────────────────────


@router.get("/{phone_number}/interactions", response_model=list[Interaction])
def list_interactions(phone_number: int) -> list[Interaction]:
    """Return all interactions for a contact."""
    record = store.contacts.get(phone_number)
    if not record:
        raise HTTPException(status_code=404, detail="Contact not found")
    return record.interactions

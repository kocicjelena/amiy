from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core.config import settings
from app.core.db import get_session
from app.models import Contact

# Session = Annotated[Session, Depends(get_session)]


def get_current_contact(session: Session = Depends(get_session)) -> Contact:
    contact = session.get(Contact, 1)  #token_data.sub) --- IGNORE ---
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if not contact:
        raise HTTPException(status_code=400, detail="Inactive contact")
    return contact


CurrentContact = Annotated[Contact, Depends(get_current_contact)]


def get_current_active_supercontact(current_contact: CurrentContact) -> Contact:
    if not current_contact:
        raise HTTPException(
            status_code=403, detail="Maybe, the contact is in conflict with existing phone numbers"
        )
    return current_contact

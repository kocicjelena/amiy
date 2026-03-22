from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────── Company ────────────────────────────


class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None


class Company(BaseModel):
    name: str
    industry: Optional[str] = None


# ──────────────────────────── Contact ────────────────────────────


class ContactCreate(BaseModel):
    name: Optional[str] = None
    phone_number: int
    role: str
    company: str                  # company name — must match a Company.name


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None


class ContactPublic(BaseModel):
    name: Optional[str]
    phone_number: int
    role: str
    company: str


# ──────────────────────────── Interaction ────────────────────────────


class InteractionCreate(BaseModel):
    notes: str = Field(min_length=1)


class Interaction(BaseModel):
    notes: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ──────────────────────────── Rich response ──────────────────────────────────


class ContactDetail(BaseModel):
    """Full contact response: contact fields + company info + interactions."""

    name: Optional[str]
    phone_number: int
    role: str
    company: Company              # full Company object (name + industry)
    interactions: list[Interaction] = []


# ──────────────────────────── Generic ────────────────────────────


class Message(BaseModel):
    message: str

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


# ──────────────────────────── Company ────────────────────────────


class CompanyBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=255)
    industry: str | None = Field(default=None, max_length=255)


class Company(CompanyBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    contacts: list["Contact"] = Relationship(back_populates="company_details")


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)


class CompanyPublic(CompanyBase):
    id: uuid.UUID


class CompaniesPublic(SQLModel):
    companies: list[CompanyPublic]
    count: int


# ──────────────────────────── Contact ────────────────────────────
# ContactsBase is kept exactly as specified — company is a plain string field.
# The FK to the Company table lives on Contact itself (not on the base) so the
# base definition is untouched, and the ORM relationship is named company_details
# to avoid a collision with the inherited company: str field.


class ContactsBase(SQLModel):
    company: str = Field(unique=True, index=True, max_length=255)
    phone_number: int = Field(unique=True)   # deduplication key
    role: str
    name: str | None = Field(default=None, max_length=255)


class Contact(ContactsBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Optional FK — a contact can exist before a Company row is created
    company_id: uuid.UUID | None = Field(
        default=None, foreign_key="company.id", ondelete="SET NULL"
    )

    # Named company_details to avoid collision with ContactsBase.company (str)
    company_details: Company | None = Relationship(back_populates="contacts")
    interactions: list["Interactions"] = Relationship(back_populates="contact")


class ContactCreate(ContactsBase):
    company_id: uuid.UUID | None = None


class ContactUpdate(SQLModel):
    """All fields optional — PATCH semantics."""

    company: str | None = Field(default=None, max_length=255)
    phone_number: int | None = None
    role: str | None = None
    name: str | None = Field(default=None, max_length=255)
    company_id: uuid.UUID | None = None


class ContactPublic(ContactsBase):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    company_details: CompanyPublic | None = None


class ContactsPublic(SQLModel):
    contacts: list[ContactPublic]
    count: int


class ContactWithInteractions(ContactPublic):
    """Full contact response: company string + company details + interactions."""

    interactions: list["InteractionsPublic"] = []


# ──────────────────────────── Interactions ────────────────────────────


class InteractionsBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class Interactions(InteractionsBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(
        foreign_key="contact.id", nullable=False, ondelete="CASCADE"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    contact: Contact | None = Relationship(back_populates="interactions")
    notes: list["Note"] = Relationship(back_populates="interaction")


class InteractionsCreate(InteractionsBase):
    pass


class InteractionsPublic(InteractionsBase):
    id: uuid.UUID
    contact_id: uuid.UUID
    timestamp: datetime
    notes: list["Note"] = []


class InteractionsList(SQLModel):
    interactions: list[InteractionsPublic]
    count: int


# ──────────────────────────── Note ────────────────────────────


class Note(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    interaction_id: uuid.UUID = Field(
        foreign_key="interactions.id", nullable=False, ondelete="CASCADE"
    )
    text: str = Field(max_length=4000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    interaction: Interactions | None = Relationship(back_populates="notes")


class NoteCreate(SQLModel):
    text: str = Field(max_length=4000)


# ──────────────────────────── Query helpers ──────────────────────────────────


class QueryRequest(SQLModel):
    phone_number: int
    interaction_ids: list[uuid.UUID] | None = None


class InteractionResult(SQLModel):
    interaction_id: uuid.UUID
    contact_id: uuid.UUID
    title: str
    description: str | None


class QueryResponse(SQLModel):
    phone_number: int
    interactions: list[InteractionResult]


# ──────────────────────────── Auth ────────────────────────────────────────────


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class Message(SQLModel):
    message: str

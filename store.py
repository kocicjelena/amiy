"""
In-memory store — replaces the database entirely.

Two plain Python dicts hold all state for the lifetime of the process:

    companies   : dict[str, Company]        keyed by company name (unique)
    contacts    : dict[int, _ContactRecord] keyed by phone_number (unique)

A _ContactRecord bundles the contact fields with its interaction list so
everything for one contact lives in a single place.
"""

from dataclasses import dataclass, field
from typing import Optional

from models import Company, Interaction


@dataclass
class _ContactRecord:
    name: Optional[str]
    phone_number: int
    role: str
    company: str                          # company name reference
    interactions: list[Interaction] = field(default_factory=list)


class _Store:
    def __init__(self) -> None:
        self.companies: dict[str, Company] = {}           # name → Company
        self.contacts: dict[int, _ContactRecord] = {}     # phone_number → record


# Module-level singleton — imported everywhere, never re-created.
store = _Store()

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import select

from app import crud
from app.api.deps import Session, get_current_active_supercontact
from app.models import (
    Company,
    CompaniesPublic,
    CompanyCreate,
    CompanyPublic,
    CompanyUpdate,
    Message,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_supercontact)]
)
def list_companies(session, skip: int = 0, limit: int = 100):
    #c = session.exec(select(Company)).one()
    #count: int = session.exec(func.count(select(Company))).one()
    companies = list(session.exec(select(Company).offset(skip).limit(limit)).all())
    return companies


@router.post(
    "/",
    dependencies=[Depends(get_current_active_supercontact)],
    status_code=201,
)
def create_company(*, session, company_in):
    if crud.get_company_by_name(session=session, name=company_in.name):
        raise HTTPException(status_code=409, detail="Company name already exists")
    return crud.create_company(session=session, company_in=company_in)


@router.get("/{company_id}")
def get_company(company_id, session):
    company = crud.get_company(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch(
    "/{company_id}",
    dependencies=[Depends(get_current_active_supercontact)],
)
def update_company(
    company_id, company_in, session
):
    company = crud.get_company(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company_in.name and company_in.name != company.name:
        if crud.get_company_by_name(session=session, name=company_in.name):
            raise HTTPException(status_code=409, detail="Company name already taken")
    return crud.update_company(session=session, db_company=company, company_in=company_in)


@router.delete(
    "/{company_id}",
    dependencies=[Depends(get_current_active_supercontact)],
)
def delete_company(company_id, session):
    company = crud.get_company(session=session, company_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    crud.delete_company(session=session, db_company=company)
    return Message(message="Company deleted successfully")

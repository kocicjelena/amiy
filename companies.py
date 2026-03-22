from fastapi import APIRouter, HTTPException

from models import Company, CompanyCreate, Message
from store import store

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=Company, status_code=201)
def create_company(company_in: CompanyCreate) -> Company:
    if company_in.name in store.companies:
        raise HTTPException(status_code=409, detail="Company already exists")
    company = Company(name=company_in.name, industry=company_in.industry)
    store.companies[company_in.name] = company
    return company


@router.get("/", response_model=list[Company])
def list_companies() -> list[Company]:
    return list(store.companies.values())


@router.get("/{name}", response_model=Company)
def get_company(name: str) -> Company:
    company = store.companies.get(name)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{name}", response_model=Message)
def delete_company(name: str) -> Message:
    if name not in store.companies:
        raise HTTPException(status_code=404, detail="Company not found")
    del store.companies[name]
    return Message(message="Company deleted")

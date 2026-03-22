from fastapi import APIRouter


from app.api.routes import contacts, interactions,companies


api_router = APIRouter()
api_router.include_router(contacts.router)
api_router.include_router(interactions.router)
api_router.include_router(companies.router)

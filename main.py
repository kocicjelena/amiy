from fastapi import FastAPI

import companies, contacts, interactions

#from app.routers import companies, contacts, interactions

app = FastAPI(
    title="CRM API",
    description="In-memory CRM — contacts, companies, and interactions.",
    version="1.0.0",
)

app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(interactions.router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok"}

from sqlmodel import Session, create_engine, SQLModel

from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


def init_db(session: Session) -> None:
    """Create all tables that don't yet exist.

    All model modules must be imported before create_all so SQLModel's
    metadata registry is fully populated.
    """
    import app.models  # noqa: F401  — registers Company, Contact, Interactions, Note

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./tictactoe.db")

engine = create_engine(DATABASE_URL, echo=True if os.environ.get("DEBUG_DB")=="1" else False)

# PUBLIC_INTERFACE
def get_session():
    """
    Dependency that returns a SQLModel Session.
    """
    with Session(engine) as session:
        yield session

# PUBLIC_INTERFACE
def init_db():
    """
    Initializes database tables. Should be called on startup if autoinit is wanted.
    """
    import logging

    logging.info("Creating all database tables (if not exist)")
    SQLModel.metadata.create_all(engine)

import os
from datetime import datetime
from functools import lru_cache

from sqlmodel import SQLModel, create_engine
from vibetracer.database.config import DB_DIRECTORY


@lru_cache(maxsize=1)
def get_engine():
    """
    Ensure the database directory exists, lazily create a timestamped SQLite engine,
    and initialize all SQLModel metadata. Cache it for all future calls.
    Returns:
        engine: SQLAlchemy engine connected to the new SQLite database.
    """
    os.makedirs(DB_DIRECTORY, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = f"{DB_DIRECTORY}/run_{timestamp}.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine

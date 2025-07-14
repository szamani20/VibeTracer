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
    db_directory = os.path.join(os.environ.get('VibeTracer_CWD', './'), DB_DIRECTORY)
    os.makedirs(db_directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = f"{db_directory}/run_{timestamp}.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine

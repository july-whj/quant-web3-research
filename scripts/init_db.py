"""Create local database tables for the initial development scaffold."""

from apps.api.app import models  # noqa: F401
from apps.api.app.db import Base, engine


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database schema is ready.")

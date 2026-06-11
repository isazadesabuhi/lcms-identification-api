from app.db.database import Base, engine
from app.db import models  # noqa: F401


def create_database():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_database()
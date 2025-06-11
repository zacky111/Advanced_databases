from src.database.model import Base
from src.database.connection import engine

def create_database():
    """
    Create the database tables defined in the Base metadata.
    """
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    create_database()

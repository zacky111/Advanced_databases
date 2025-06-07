from src.database.connection import engine
from sqlalchemy import inspect, text

def drop_all_tables():
    inspector = inspect(engine)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Disable FK constraints
            conn.execute(text("SET session_replication_role = 'replica';"))
            # Drop all tables
            for table_name in inspector.get_table_names():
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
            # Enable FK constraints
            conn.execute(text("SET session_replication_role = 'origin';"))
            trans.commit()
            print("All tables dropped successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Error: {e}")

if __name__ == "__main__":
    drop_all_tables()
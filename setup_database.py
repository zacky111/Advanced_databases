from src.database.connection import engine
from src.database.create import create_database
from src.database.data_insert import import_data
from sqlalchemy.orm import Session

if __name__ == "__main__":
    with Session(engine) as session:
        create_database()
        import_data(session, csv_path='data/covid-fci-data-cleaned.csv')
        print("Database setup and data import completed successfully.")
    print("You can now run the application with: streamlit run streamlit_app.py")


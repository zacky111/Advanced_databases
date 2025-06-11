from db_connect import engine
from src.database.model import Base
from sqlalchemy import inspect

inspector = inspect(engine)

def print_db_structure(output_file="db_structure.txt"):
    with open(output_file, "w") as f:
        for table_name in inspector.get_table_names():
            f.write(f"Table: {table_name}\n")
            columns = inspector.get_columns(table_name)
            for column in columns:
                col_line = f"  Column: {column['name']} ({column['type']})"
                if column.get('primary_key'):
                    col_line += " [PK]"
                f.write(col_line + "\n")
            f.write("\n")

if __name__ == "__main__":
    print_db_structure()
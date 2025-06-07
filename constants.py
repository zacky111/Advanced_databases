import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

PG_USERNAME = os.getenv('PG_USERNAME')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

# print(f"PostgreSQL connection details loaded: {PG_USERNAME}, {PG_HOST}, {PG_PORT}, {PG_DATABASE}")


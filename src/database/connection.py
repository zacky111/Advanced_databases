from sqlalchemy.engine import URL, create_engine
from constants import PG_USERNAME, PG_PASSWORD, PG_HOST, PG_PORT, PG_DATABASE
from src.utils.log import get_logger

logger = get_logger("sqlalchemy")

connect_url = URL.create(
    'postgresql+psycopg2',
    username=PG_USERNAME,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE
)

engine = create_engine(connect_url, echo=False)
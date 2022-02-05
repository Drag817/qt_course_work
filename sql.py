import psycopg2
from config import *

connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )

connection.autocommit = True

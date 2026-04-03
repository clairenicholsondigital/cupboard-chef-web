import psycopg
from contextlib import contextmanager


DATABASE_URL = "postgresql://cupboardchef:Tennis2!@172.17.0.1:32770/cupboardchef_db"


@contextmanager
def get_conn():
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL)
        yield conn
    finally:
        if conn is not None:
            conn.close()
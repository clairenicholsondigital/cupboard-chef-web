import os
from contextlib import contextmanager
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cupboardchef:Tennis2!@127.0.0.1:5432/cupboardchef_db")

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

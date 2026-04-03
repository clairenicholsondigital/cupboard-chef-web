import os
import psycopg
from contextlib import contextmanager

# Use env var if available, fallback to working Docker hostname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cupboardchef:Tennis2!@postgresql:5432/cupboardchef_db"
)

@contextmanager
def get_conn():
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL)
        yield conn
    finally:
        if conn is not None:
            conn.close()
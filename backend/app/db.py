import os
import psycopg
from contextlib import contextmanager

# Prefer env var, fallback to working Docker connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://helixscribe:Tennisandy23!@postgresql-ktbx-postgresql-1:5432/helixscribe"
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

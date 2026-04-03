import psycopg
from contextlib import contextmanager


DATABASE_URL = "postgresql://cupboardchef:Tennis2!@postgresql-pbtcx:5432/cupboardchef_db"


@contextmanager
def get_conn():
    conn = None
    try:
        conn = psycopg.connect(DATABASE_URL)
        yield conn
    except Exception as exc:
        print(f"Database connection/query error: {exc}")
        raise
    finally:
        if conn is not None:
            conn.close()
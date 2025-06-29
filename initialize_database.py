import psycopg2
import os
from models import get_sql_schema # models.py now returns PostGIS DDL

DB_NAME = os.getenv("PGDATABASE", "offers_db")
DB_USER = os.getenv("PGUSER", "offer_user")
DB_PASSWORD = os.getenv("PGPASSWORD", "offer_password")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")

def create_database_tables_postgres():
    """
    Connects to the PostgreSQL database and creates all necessary tables using PostGIS schema.
    Assumes the database and user already exist and PostGIS extension is enabled.
    """

    print(f"Initializing PostGIS tables in database: {DB_NAME} on {DB_HOST}:{DB_PORT}...")

    conn = None
    cursor = None
    try:
        conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        print("Connected to PostgreSQL successfully.")

        # Get DDL statements
        sql_schema_ddl = get_sql_schema()

        print("Executing PostGIS DDL to create tables and indexes...")
        cursor.execute(sql_schema_ddl)
        conn.commit()
        print("Database tables and indexes created successfully (or already existed).")

        # Optional: Verify table creation by listing tables from information_schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print("\nTables in the database (public schema):")
        if tables:
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No tables found in public schema. This might be an issue.")
            # Check for spatial_ref_sys to confirm PostGIS is somewhat there
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'spatial_ref_sys');")
            if cursor.fetchone()[0]:
                print("Found 'spatial_ref_sys' table, PostGIS extension is likely active.")
            else:
                print("Warning: 'spatial_ref_sys' not found. PostGIS extension might not be active.")


    except psycopg2.Error as e:
        print(f"A PostgreSQL error occurred during database initialization: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    # This script assumes the DB and user are created, and PostGIS extension is enabled.
    # It primarily focuses on creating the application-specific tables.
    # No check for existing DB file like in SQLite version, as PG is a server.
    create_database_tables_postgres()

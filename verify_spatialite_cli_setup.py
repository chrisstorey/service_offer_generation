import sqlite3
import os
import subprocess

db_path = "test_spatialite_cli_setup.db"

if os.path.exists(db_path):
    os.remove(db_path)

conn = None

def run_spatialite_sql(db, sql_command):
    """Helper to run SQL commands using spatialite CLI"""
    # Using a heredoc for potentially complex SQL
    cmd = f"spatialite {db} <<EOF\n{sql_command}\nEOF"
    print(f"Executing via spatialite CLI: {sql_command}")
    process = subprocess.run(cmd, shell=True, executable='/bin/bash', capture_output=True, text=True)
    if process.returncode != 0:
        print(f"SpatiaLite CLI command failed. stdout: {process.stdout}, stderr: {process.stderr}")
        raise Exception(f"SpatiaLite CLI execution failed for: {sql_command}")
    print(f"SpatiaLite CLI stdout: {process.stdout.strip()}")
    print(f"SpatiaLite CLI stderr: {process.stderr.strip()}") # Often prints query results or "1" on success
    return process

try:
    # Step 1: Create an empty DB file (some spatialite CLIs prefer the file to exist)
    open(db_path, 'a').close()
    print(f"Created empty DB file: {db_path}")

    # Step 2: Initialize SpatiaLite & Create Schema using 'spatialite' CLI
    # InitSpatialMetaData must be run first on a new SpatiaLite DB.
    run_spatialite_sql(db_path, "SELECT InitSpatialMetaData(1);")
    print("Attempted InitSpatialMetaData via CLI.")

    # Create table and geometry column via CLI
    run_spatialite_sql(db_path, """
    CREATE TABLE IF NOT EXISTS test_geom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    );
    SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');
    """)
    print("Table 'test_geom' and its geometry column created via CLI.")

    # Step 3: Connect with Python's sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Python sqlite3 connection successful.")

    # Step 4: Verify SpatiaLite functions are usable via SQL from Python
    # (because the DB is now a fully initialized SpatiaLite DB)
    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version via Python SQL: {version}")

    # Step 5: Insert and retrieve data using SpatiaLite SQL functions from Python
    # Note: No enable_load_extension or load_extension needed here,
    # as we're relying on the database file being "live" with SpatiaLite.
    cursor.execute("INSERT INTO test_geom (name, geom) VALUES (?, MakePoint(?, ?, 4326));", ('test_py_insert', 50.0, 60.0))
    conn.commit()
    print("Inserted a point using MakePoint via Python SQL.")

    cursor.execute("SELECT id, name, AsText(geom) FROM test_geom WHERE name = 'test_py_insert';")
    result = cursor.fetchone()
    print(f"Retrieved geometry via Python SQL: {result}")

    if not result:
        print("Failed to retrieve the inserted point.")
        exit(1)

    expected_geom_texts = ["POINT(50 60)", "POINT(50.0 60.0)"]
    if result[2] not in expected_geom_texts:
        print(f"Retrieved geometry text '{result[2]}' does not match expected formats {expected_geom_texts}.")
        exit(1)
    print(f"Geometry text '{result[2]}' matches an expected format.")

    print("SpatiaLite setup (CLI-based) and Python sqlite3 integration (SQL functions) verification successful!")

except sqlite3.Error as e:
    print(f"An SQLite/Python error occurred: {e}")
    if "no such function" in str(e).lower():
        print("CRITICAL: SpatiaLite SQL functions (e.g., spatialite_version, MakePoint) are not recognized even after CLI setup.")
        print("This implies the Python sqlite3 module cannot use functions from a CLI-initialized SpatiaLite DB,")
        print("or the CLI initialization itself did not fully succeed in making SpatiaLite active for the DB file.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("Cleanup: Test database removed.")

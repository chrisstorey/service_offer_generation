import sqlite3
import os
import subprocess

db_path = "test_spatialite_cli.db"

# Clean up previous test db if it exists
if os.path.exists(db_path):
    os.remove(db_path)

conn = None

try:
    # 1. Use 'spatialite' CLI to create and initialize the database
    # Create an empty DB file first for spatialite CLI to open
    open(db_path, 'a').close()

    # Initialize SpatiaLite using the CLI.
    # Some versions of spatialite CLI might expect the DB to exist or use a different command.
    # If 'spatialite test_spatialite_cli.db "SELECT InitSpatialMetaData();"' fails,
    # it might be because it needs to be run in interactive mode or via a script file.
    # A common way is to echo commands into it or use a .sql file.

    # Try direct command execution first
    init_command = f"spatialite {db_path} \"SELECT InitSpatialMetaData(1);\""
    process = subprocess.run(init_command, shell=True, capture_output=True, text=True)

    if process.returncode != 0:
        print(f"SpatiaLite CLI initialization attempt 1 failed. stderr: {process.stderr}")
        # Fallback: Create the database with sqlite3, then try to initialize with spatialite CLI
        # This is more robust as spatialite CLI sometimes has issues creating a new DB and initializing in one go.
        subprocess.run(f"sqlite3 {db_path} \".quit\"", shell=True, check=True) # Creates an empty SQLite DB
        init_command_v2 = f"spatialite {db_path} < <(echo 'SELECT InitSpatialMetaData(1);')"
        process = subprocess.run(init_command_v2, shell=True, executable='/bin/bash', capture_output=True, text=True)
        if process.returncode != 0:
            print(f"SpatiaLite CLI initialization attempt 2 failed. stderr: {process.stderr}")
            # Final fallback: try to create the DB and initialize it from within spatialite's SQL interface directly
            # This is often the most reliable for ensuring InitSpatialMetaData runs.
            sql_init_script = "SELECT InitSpatialMetaData(1);"
            init_command_v3 = f"spatialite {db_path} \"{sql_init_script}\""
            # Some spatialite versions might need .read for commands from file or stdin
            # For now, stick to direct command if possible.
            # If the above still fails, it indicates a deeper issue with spatialite CLI or environment.
            # One last attempt with a script file for spatialite CLI
            with open("init_spatial.sql", "w") as f:
                f.write("SELECT InitSpatialMetaData(1);\n")
            init_command_v4 = f"spatialite {db_path} < init_spatial.sql"
            process = subprocess.run(init_command_v4, shell=True, capture_output=True, text=True)
            if os.path.exists("init_spatial.sql"): os.remove("init_spatial.sql")

            if process.returncode != 0:
                 print(f"SpatiaLite CLI initialization attempt 4 (with script) failed. stderr: {process.stderr}")
                 # If all attempts fail, raise an error.
                 raise Exception(f"Failed to initialize SpatiaLite DB using CLI. stderr: {process.stderr}")

    print("SpatiaLite database initialized via CLI (or an attempt was made).")

    # 2. Connect to the pre-initialized database with Python's sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Standard library sqlite3 connection successful to pre-initialized DB.")

    # 3. Check if SpatiaLite functions are available (no need to load_extension)
    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version: {version}")

    # 4. Perform a simple SpatiaLite geometry operation
    cursor.execute("DROP TABLE IF EXISTS test_geom;")
    cursor.execute("CREATE TABLE test_geom (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);")
    # The AddGeometryColumn function should be available if SpatiaLite is active
    cursor.execute("SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');")
    conn.commit() # Commit AddGeometryColumn as it modifies db schema
    print("Created table with geometry column using SpatiaLite SQL function.")

    cursor.execute("INSERT INTO test_geom (name, geom) VALUES (?, MakePoint(?, ?, 4326));", ('test_point_cli', 15.0, 25.0))
    conn.commit()
    print("Inserted a point geometry using SpatiaLite SQL function.")

    cursor.execute("SELECT id, name, AsText(geom) FROM test_geom WHERE name = 'test_point_cli';")
    result = cursor.fetchone()
    print(f"Retrieved geometry: {result}")

    if not result:
        print("Failed to retrieve the inserted point.")
        exit(1)

    expected_geom_text = "POINT(15 25)"
    # Allow for floating point representation as well e.g. POINT(15.0 25.0)
    if result[2] not in [expected_geom_text, "POINT(15.0 25.0)"]:
        print(f"Retrieved geometry text '{result[2]}' does not match expected '{expected_geom_text}' or 'POINT(15.0 25.0)'.")
        exit(1)
    print(f"Geometry text '{result[2]}' matches expected format.")

    print("SpatiaLite setup verification successful using CLI initialization and standard sqlite3!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    # Check if the error is "no such function: MakePoint" or "AddGeometryColumn"
    if "no such function" in str(e).lower():
        print("This indicates SpatiaLite functions are not available. The DB might not have been correctly initialized or SpatiaLite is not properly linked/active.")
    exit(1)
except subprocess.CalledProcessError as e:
    print(f"A subprocess error occurred: {e}")
    print(f"Stderr: {e.stderr}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists("init_spatial.sql"): # cleanup script if created
        os.remove("init_spatial.sql")

import sqlite3
import os
import subprocess

db_path = "test_spatialite_final.db"

if os.path.exists(db_path):
    os.remove(db_path)

conn = None

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Standard library sqlite3 connection successful.")

    # Step 1: Enable extension loading for this connection
    conn.enable_load_extension(True)
    print("Extension loading enabled for the current Python sqlite3 connection.")

    # Step 2: Load the SpatiaLite module
    loaded_ext = False
    try:
        conn.load_extension('mod_spatialite')
        print("Loaded SpatiaLite extension 'mod_spatialite' into Python's sqlite3 connection.")
        loaded_ext = True
    except sqlite3.OperationalError as e_direct_load:
        print(f"Failed to load 'mod_spatialite' directly: {e_direct_load}")
        # Try to find the .so file directly if the simple name fails
        find_cmd = 'find /usr/lib -name "mod_spatialite*.so" -print -quit 2>/dev/null'
        mod_path_process = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
        mod_path = mod_path_process.stdout.strip()
        if mod_path:
            print(f"Found SpatiaLite module at: {mod_path}")
            try:
                conn.load_extension(mod_path)
                print(f"Loaded SpatiaLite extension from path '{mod_path}'.")
                loaded_ext = True
            except sqlite3.OperationalError as e_path_load:
                print(f"Failed to load SpatiaLite module by specific path '{mod_path}': {e_path_load}")
        else:
            print("SpatiaLite module .so file not found by find command in /usr/lib.")

    if not loaded_ext:
        print("Failed to load SpatiaLite extension into Python. SpatiaLite functions will not be available.")
        exit(1)

    # Step 3: Initialize Spatial MetaData (recommended after loading extension on a new DB)
    try:
        # Using 0 instead of 1 for the argument to avoid potential transaction errors on some versions if not needed.
        # If this fails because it's already initialized (e.g. if db somehow persisted and was init), that's okay.
        cursor.execute("SELECT InitSpatialMetaData();")
        print("Spatial metadata initialized for the database via Python connection.")
    except sqlite3.OperationalError as e_init:
        print(f"Could not initialize spatial metadata (perhaps already done, or another issue): {e_init}")
        if "already initialized" not in str(e_init).lower() and "transaction" not in str(e_init).lower() : # common non-fatal messages
             # If it's some other error, then it might be a problem
             print("Warning: InitSpatialMetaData() failed with an unexpected error.")


    # Step 4: Verify SpatiaLite functions are now available
    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version confirmed via SQL: {version}")

    # Step 5: Perform a simple SpatiaLite geometry operation
    cursor.execute("DROP TABLE IF EXISTS test_geom;") # Clean slate
    cursor.execute("CREATE TABLE test_geom (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);")
    conn.commit()

    cursor.execute("SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');")
    conn.commit()
    print("Created table with geometry column using AddGeometryColumn.")

    cursor.execute("INSERT INTO test_geom (name, geom) VALUES (?, MakePoint(?, ?, 4326));", ('test_point_py', 30.0, 40.0))
    conn.commit()
    print("Inserted a point geometry using MakePoint.")

    cursor.execute("SELECT id, name, AsText(geom) FROM test_geom WHERE name = 'test_point_py';")
    result = cursor.fetchone()
    print(f"Retrieved geometry: {result}")

    if not result:
        print("Failed to retrieve the inserted point.")
        exit(1)

    expected_geom_text_major = "POINT(30 40)"
    expected_geom_text_minor = "POINT(30.0 40.0)" # Some versions include .0
    if result[2] not in [expected_geom_text_major, expected_geom_text_minor]:
        print(f"Retrieved geometry text '{result[2]}' does not match expected formats.")
        exit(1)
    print(f"Geometry text '{result[2]}' matches an expected format.")

    print("SpatiaLite setup and Python sqlite3 integration verification successful!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    if "no such function" in str(e).lower() or "has no function named" in str(e).lower():
        print("This indicates SpatiaLite SQL functions are not available. Ensure the extension was loaded correctly.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred during Python script execution: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

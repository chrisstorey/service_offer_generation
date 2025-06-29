import sqlite3
import os

db_path = "test_spatialite_std.db"

# Clean up previous test db if it exists
if os.path.exists(db_path):
    os.remove(db_path)

conn = None  # Initialize conn to None

try:
    # 1. Connect to SQLite and create a database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Standard library sqlite3 connection successful.")

    # 2. Enable SpatiaLite extension loading
    conn.enable_load_extension(True)
    print("Extension loading enabled using standard sqlite3.")

    # 3. Load SpatiaLite extension
    # The package libsqlite3-mod-spatialite should install it in a standard path.
    # On Ubuntu, this is often just 'mod_spatialite' or 'libspatialite.so'
    # or the full path to the .so file.

    loaded_successfully = False
    # First, try the conventional name provided by libsqlite3-mod-spatialite
    try:
        cursor.execute("SELECT load_extension('mod_spatialite')")
        print("SpatiaLite extension 'mod_spatialite' loaded successfully.")
        loaded_successfully = True
    except sqlite3.OperationalError as e:
        print(f"Failed to load 'mod_spatialite': {e}")
        # Fallback: try to find the .so file directly if the simple name fails
        find_output = os.popen('find /usr/lib -name "mod_spatialite*.so" -print -quit 2>/dev/null').read().strip()
        if find_output:
            print(f"Found potential extension at: {find_output}")
            try:
                cursor.execute(f"SELECT load_extension('{find_output}')")
                print(f"SpatiaLite extension '{find_output}' loaded successfully.")
                loaded_successfully = True
            except sqlite3.OperationalError as e_path:
                 print(f"Failed to load found extension '{find_output}': {e_path}")
        else:
            print("mod_spatialite*.so not found in /usr/lib via find command.")

    if not loaded_successfully:
        print("Could not load SpatiaLite extension. Verification failed.")
        exit(1)

    # 4. Initialize Spatial MetaData
    try:
        cursor.execute("SELECT InitSpatialMetaData(1);")
        print("Spatial metadata initialized.")
    except sqlite3.OperationalError as e:
        print(f"Could not initialize spatial metadata (might be already initialized or other issue): {e}")
        # Check if it's because it's already initialized, which is fine
        if "already initialized" not in str(e).lower():
            # If it's some other error, then it's a problem
            raise

    # 5. Perform a simple SpatiaLite query
    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version: {version}")

    cursor.execute("DROP TABLE IF EXISTS test_geom;") # Drop if exists from previous failed run
    cursor.execute("CREATE TABLE test_geom (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);")
    # Initialize the geometry column with SRID 4326 (WGS 84)
    cursor.execute("SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');")
    print("Created table with geometry column.")

    # Insert a point using WKT and SRID
    cursor.execute("INSERT INTO test_geom (name, geom) VALUES (?, MakePoint(?, ?, 4326));", ('test_point', 10.0, 20.0))
    conn.commit()
    print("Inserted a point geometry.")

    cursor.execute("SELECT id, name, AsText(geom) FROM test_geom WHERE name = 'test_point';")
    result = cursor.fetchone()
    print(f"Retrieved geometry: {result}")

    if not result:
        print("Failed to retrieve the inserted point.")
        exit(1)
    if result[2] != "POINT(10 20)": # SpatiaLite typically doesn't include .0 for integers
        print(f"Retrieved geometry text '{result[2]}' does not match expected 'POINT(10 20)'.")
        # Accept POINT(10.0 20.0) as well
        if result[2] != "POINT(10.0 20.0)":
             exit(1)
        print("Accepted alternative format POINT(10.0 20.0)")


    print("SpatiaLite setup verification successful using standard library sqlite3!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path) # Clean up test database

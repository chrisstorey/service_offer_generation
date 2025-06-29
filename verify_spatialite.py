import sqlite3
import os

db_path = "test_spatialite.db"

# Clean up previous test db if it exists
if os.path.exists(db_path):
    os.remove(db_path)

try:
    # 1. Connect to SQLite and create a database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("SQLite connection successful.")

    # 2. Enable SpatiaLite extension loading
    conn.enable_load_extension(True)
    print("Extension loading enabled.")

    # 3. Load SpatiaLite extension
    # Try common names for the extension module
    spatialite_extensions = [
        'mod_spatialite.so', # Common on Linux
        'mod_spatialite',    # Sometimes works without .so
        'libspatialite.so',  # Another common name
        # Add paths if necessary, e.g., from
    ]
    loaded_successfully = False
    for ext_name in spatialite_extensions:
        try:
            cursor.execute(f"SELECT load_extension('{ext_name}')")
            print(f"SpatiaLite extension '{ext_name}' loaded successfully.")
            loaded_successfully = True
            break
        except sqlite3.OperationalError as e:
            print(f"Failed to load '{ext_name}': {e}")

    if not loaded_successfully:
        print("Could not load SpatiaLite extension with common names.")
        # Try to find it
        find_output = os.popen('find /usr -name "mod_spatialite*.so" 2>/dev/null').read().strip()
        if find_output:
            print(f"Found potential extension at: {find_output}")
            try:
                cursor.execute(f"SELECT load_extension('{find_output.splitlines()[0]}')")
                print(f"SpatiaLite extension '{find_output.splitlines()[0]}' loaded successfully.")
                loaded_successfully = True
            except sqlite3.OperationalError as e:
                 print(f"Failed to load found extension '{find_output.splitlines()[0]}': {e}")
        else:
            print("mod_spatialite*.so not found in /usr.")


    if loaded_successfully:
        # 4. Initialize Spatial MetaData (optional if db is new and SpatiaLite auto-initializes)
        try:
            cursor.execute("SELECT InitSpatialMetaData(1);") # 1 enables transactions for speed
            print("Spatial metadata initialized.")
        except sqlite3.OperationalError as e:
            # This might fail if already initialized, which is okay.
            print(f"Could not initialize spatial metadata (might be already initialized or other issue): {e}")


        # 5. Perform a simple SpatiaLite query
        cursor.execute("SELECT spatialite_version();")
        version = cursor.fetchone()[0]
        print(f"SpatiaLite version: {version}")

        cursor.execute("CREATE TABLE test_geom (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);")
        cursor.execute("SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');")
        print("Created table with geometry column.")

        cursor.execute("INSERT INTO test_geom (name, geom) VALUES ('test_point', MakePoint(10.0, 20.0, 4326));")
        conn.commit()
        print("Inserted a point geometry.")

        cursor.execute("SELECT id, name, AsText(geom) FROM test_geom;")
        result = cursor.fetchone()
        print(f"Retrieved geometry: {result}")
        assert result[2] == "POINT(10 20)"
        print("SpatiaLite setup verification successful!")

    else:
        print("SpatiaLite extension could not be loaded. Verification failed.")
        exit(1)

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if 'conn' in locals() and conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path) # Clean up test database

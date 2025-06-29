import sqlite3
import os
import subprocess

print("Attempting in-memory SpatiaLite setup...")
conn = None

try:
    # Step 1: Connect to an in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    print("Connected to in-memory SQLite database.")

    # Step 2: Enable extension loading
    # This is the critical step that has been failing.
    try:
        conn.enable_load_extension(True)
        print("Successfully called enable_load_extension(True).")
    except AttributeError:
        print("AttributeError: This Python's sqlite3.Connection object does not have 'enable_load_extension'.")
        print("This means it was compiled without extension support. Cannot proceed with loading SpatiaLite.")
        exit(1)
    except sqlite3.NotSupportedError:
        print("sqlite3.NotSupportedError: Extension loading is not supported by this SQLite build.")
        exit(1)


    # Step 3: Load the SpatiaLite extension module
    # Try common names/paths. 'mod_spatialite' is typical when libsqlite3-mod-spatialite is installed.
    loaded_successfully = False
    extensions_to_try = ['mod_spatialite']

    # Attempt to find the .so file path as a fallback
    find_cmd = 'find /usr/lib -name "mod_spatialite*.so" -print -quit 2>/dev/null'
    mod_path_process = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
    found_mod_path = mod_path_process.stdout.strip()
    if found_mod_path:
        print(f"Found SpatiaLite module via find: {found_mod_path}")
        extensions_to_try.append(found_mod_path)
    else:
        print("Could not find mod_spatialite*.so in /usr/lib using find.")

    for ext_name in extensions_to_try:
        try:
            cursor.execute(f"SELECT load_extension('{ext_name}')") # Use SQL load_extension
            # Or conn.load_extension(ext_name) # Python API direct load
            print(f"SpatiaLite extension '{ext_name}' loaded successfully using SQL load_extension().")
            loaded_successfully = True
            break
        except sqlite3.OperationalError as e:
            print(f"Failed to load '{ext_name}' using SQL load_extension(): {e}")
            try:
                conn.load_extension(ext_name) # Try Python API direct load
                print(f"SpatiaLite extension '{ext_name}' loaded successfully using conn.load_extension().")
                loaded_successfully = True
                break
            except sqlite3.OperationalError as e_py_load:
                 print(f"Failed to load '{ext_name}' using conn.load_extension(): {e_py_load}")


    if not loaded_successfully:
        print("Failed to load SpatiaLite extension module into the in-memory database.")
        print("Ensure 'libsqlite3-mod-spatialite' is correctly installed and accessible.")
        exit(1)

    # Step 4: Initialize SpatiaLite metadata
    try:
        cursor.execute("SELECT InitSpatialMetaData();")
        print("Spatial metadata initialized for the in-memory database.")
    except sqlite3.OperationalError as e:
        # This might fail if already initialized (less likely for in-memory unless loaded weirdly)
        # or if there's another problem.
        print(f"Could not initialize spatial metadata: {e}")
        if "already initialized" not in str(e).lower() and "transaction" not in str(e).lower():
            raise # Re-raise if it's not a common non-fatal error

    # Step 5: Verify by checking SpatiaLite version
    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version: {version}")

    # Step 6: Perform a simple geometry operation
    cursor.execute("CREATE TABLE test_geom_inmemory (id INTEGER PRIMARY KEY, name TEXT);")
    cursor.execute("SELECT AddGeometryColumn('test_geom_inmemory', 'geom', 4326, 'POINT', 'XY');")
    conn.commit()
    print("Created table with geometry column in-memory.")

    cursor.execute("INSERT INTO test_geom_inmemory (id, name, geom) VALUES (1, 'test_point', MakePoint(10.0, 20.0, 4326));")
    conn.commit()
    print("Inserted a point geometry in-memory.")

    cursor.execute("SELECT AsText(geom) FROM test_geom_inmemory WHERE id = 1;")
    geom_text = cursor.fetchone()[0]
    print(f"Retrieved geometry as text: {geom_text}")

    expected_texts = ["POINT(10 20)", "POINT(10.0 20.0)"]
    if geom_text not in expected_texts:
        print(f"Retrieved geometry '{geom_text}' does not match expected {expected_texts}")
        exit(1)

    print("In-memory SpatiaLite setup and basic operations verified successfully!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    print("Test finished.")

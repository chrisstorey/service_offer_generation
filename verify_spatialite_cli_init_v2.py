import sqlite3
import os
import subprocess

db_path = "test_spatialite_cli_v2.db"

if os.path.exists(db_path):
    os.remove(db_path)

conn = None

try:
    # Check if spatialite CLI is available
    spatialite_cli_path = ""
    if subprocess.run("command -v spatialite", shell=True, capture_output=True).returncode == 0:
        spatialite_cli_path = "spatialite"
    elif subprocess.run("command -v spatialite_cli", shell=True, capture_output=True).returncode == 0: # some systems use spatialite_cli
        spatialite_cli_path = "spatialite_cli"
    else:
        print("SpatiaLite CLI command (spatialite or spatialite_cli) not found. Cannot initialize DB via CLI.")
        # Try to load extension directly if libsqlite3-mod-spatialite was installed
        print("Attempting to load libsqlite3-mod-spatialite directly with Python's sqlite3...")
        conn = sqlite3.connect(db_path)
        conn.enable_load_extension(True)

        loaded_ext = False
        try:
            conn.load_extension('mod_spatialite')
            print("Loaded 'mod_spatialite' successfully.")
            loaded_ext = True
        except sqlite3.OperationalError as e_direct_load:
            print(f"Failed to load 'mod_spatialite': {e_direct_load}")
            try:
                # Try full path if known (usually /usr/lib/x86_64-linux-gnu/mod_spatialite.so or similar)
                # This is a guess, actual path might vary
                find_cmd = 'find /usr/lib -name "mod_spatialite*.so" -print -quit 2>/dev/null'
                mod_path_process = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
                mod_path = mod_path_process.stdout.strip()
                if mod_path:
                    print(f"Found SpatiaLite module at: {mod_path}")
                    conn.load_extension(mod_path)
                    print(f"Loaded '{mod_path}' successfully.")
                    loaded_ext = True
                else:
                    print("SpatiaLite module .so file not found in common /usr/lib paths.")
            except sqlite3.OperationalError as e_path_load:
                print(f"Failed to load SpatiaLite module by path: {e_path_load}")

        if not loaded_ext:
            print("Failed to make SpatiaLite available via direct load_extension.")
            exit(1)
        # If loaded, proceed to initialize metadata
        cursor = conn.cursor()
        cursor.execute("SELECT InitSpatialMetaData(1);")
        print("Spatial metadata initialized via direct load_extension.")

    if spatialite_cli_path:
        print(f"Using SpatiaLite CLI: {spatialite_cli_path}")
        # 1. Use 'spatialite' CLI to create and initialize the database
        open(db_path, 'a').close() # Ensure DB file exists

        # Attempting initialization using a heredoc for commands
        init_script_content = "SELECT InitSpatialMetaData(1);"
        init_command = f"{spatialite_cli_path} {db_path} <<EOF\n{init_script_content}\nEOF"

        process = subprocess.run(init_command, shell=True, executable='/bin/bash', capture_output=True, text=True)

        if process.returncode != 0:
            print(f"SpatiaLite CLI initialization failed. stdout: {process.stdout}, stderr: {process.stderr}")
            # Fallback for some CLI versions that might not like heredoc input for single commands well
            # or if the DB needs to be created by sqlite3 first for spatialite CLI to attach.
            subprocess.run(f"sqlite3 {db_path} \".quit\"", shell=True, check=True) # Creates an empty SQLite DB
            init_command_v2 = f"{spatialite_cli_path} {db_path} \"{init_script_content}\"" # Direct command string
            process = subprocess.run(init_command_v2, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                print(f"SpatiaLite CLI initialization attempt 2 failed. stdout: {process.stdout}, stderr: {process.stderr}")
                raise Exception(f"Failed to initialize SpatiaLite DB using CLI. stderr: {process.stderr}")

        print("SpatiaLite database initialized via CLI.")
        if conn: conn.close() # Close connection from direct load attempt if it was opened
        conn = sqlite3.connect(db_path) # Reconnect to CLI-initialized DB
        cursor = conn.cursor()


    print("Standard library sqlite3 connection successful.")

    cursor.execute("SELECT spatialite_version();")
    version = cursor.fetchone()[0]
    print(f"SpatiaLite version: {version}")

    cursor.execute("DROP TABLE IF EXISTS test_geom;")
    cursor.execute("CREATE TABLE test_geom (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);")
    cursor.execute("SELECT AddGeometryColumn('test_geom', 'geom', 4326, 'POINT', 'XY');")
    conn.commit()
    print("Created table with geometry column.")

    cursor.execute("INSERT INTO test_geom (name, geom) VALUES (?, MakePoint(?, ?, 4326));", ('test_point_cli_v2', 15.0, 25.0))
    conn.commit()
    print("Inserted a point geometry.")

    cursor.execute("SELECT id, name, AsText(geom) FROM test_geom WHERE name = 'test_point_cli_v2';")
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

    print("SpatiaLite setup verification successful!")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    if "no such function" in str(e).lower() or "has no function named" in str(e).lower():
        print("This indicates SpatiaLite functions are not available. The DB might not have been correctly initialized or SpatiaLite is not properly linked/active.")
    exit(1)
except subprocess.CalledProcessError as e:
    print(f"A subprocess error occurred: {e}")
    if e.stderr: print(f"Stderr: {e.stderr}")
    if e.stdout: print(f"Stdout: {e.stdout}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if conn:
        conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

import psycopg2
import os

DB_NAME = os.getenv("PGDATABASE", "offers_db")
DB_USER = os.getenv("PGUSER", "offer_user")
DB_PASSWORD = os.getenv("PGPASSWORD", "offer_password") # Get from env or use fixed for test
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")

conn = None
try:
    conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
    print(f"Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    print("PostgreSQL connection successful.")

    # Check PostGIS version
    cursor.execute("SELECT PostGIS_full_version();")
    postgis_version = cursor.fetchone()[0]
    print(f"PostGIS version: {postgis_version}")

    # Perform a simple PostGIS operation
    cursor.execute("CREATE TABLE IF NOT EXISTS test_gis (id SERIAL PRIMARY KEY, name TEXT, geom GEOMETRY(Point, 4326));")
    conn.commit()
    print("Created test_gis table with a PostGIS geometry column.")

    # Insert a point using PostGIS function
    test_lon, test_lat = -1.78, 53.64 # Example coordinates
    cursor.execute(
        "INSERT INTO test_gis (name, geom) VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));",
        ("Test Point", test_lon, test_lat)
    )
    conn.commit()
    print(f"Inserted test point at ({test_lon}, {test_lat}).")

    # Retrieve and verify the point
    cursor.execute("SELECT id, name, ST_AsText(geom) FROM test_gis WHERE name = 'Test Point';")
    result = cursor.fetchone()
    print(f"Retrieved: ID={result[0]}, Name={result[1]}, Geom_WKT={result[2]}")

    expected_wkt = f"POINT({test_lon} {test_lat})"
    if result[2] == expected_wkt:
        print("PostGIS setup and basic operation verification successful!")
    else:
        print(f"Verification FAILED: Expected WKT '{expected_wkt}', but got '{result[2]}'")
        exit(1)

    # Clean up
    cursor.execute("DROP TABLE test_gis;")
    conn.commit()
    print("Cleaned up test_gis table.")

except psycopg2.Error as e:
    print(f"A PostgreSQL error occurred: {e}")
    if conn: conn.rollback() # Rollback on error
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("PostgreSQL connection closed.")

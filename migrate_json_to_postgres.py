import json
import psycopg2
import psycopg2.extras # For DictCursor or extras
import uuid
import os # <--- IMPORT OS
from typing import List, Dict, Any, Optional
from datetime import time, date

from models import (
    OrganisationDB, LocationDB, OfferDB, CostOptionDB,
    ServiceScheduleDB, ServiceAreaDB
) # Using DB models for structure

SOURCE_JSON_FILE = "offers.json"
DB_NAME = os.getenv("PGDATABASE", "offers_db")
DB_USER = os.getenv("PGUSER", "offer_user")
DB_PASSWORD = os.getenv("PGPASSWORD", "offer_password")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")

def migrate_data_postgres():
    print(f"Starting migration from {SOURCE_JSON_FILE} to PostgreSQL database {DB_NAME}...")

    try:
        with open(SOURCE_JSON_FILE, "r") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Source JSON file '{SOURCE_JSON_FILE}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{SOURCE_JSON_FILE}': {e}")
        return

    conn = None
    cursor = None
    try:
        conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
        conn = psycopg2.connect(conn_string)
        # cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # Useful for fetching by col name
        cursor = conn.cursor()
        print("Connected to PostgreSQL database.")

        inserted_org_ids: Dict[str, str] = {}
        inserted_loc_ids: Dict[str, str] = {}

        for item_data in raw_data:
            original_offer_id = item_data.get("id", str(uuid.uuid4()))

            # 1. Organisation
            org_data_json = item_data.get("organisation")
            db_org_id = None
            if org_data_json and isinstance(org_data_json, dict):
                original_org_id = org_data_json.get("id")
                if not original_org_id:
                    print(f"Warning: Org data missing 'id' in offer '{original_offer_id}'. Skipping.")
                    continue
                if original_org_id in inserted_org_ids:
                    db_org_id = inserted_org_ids[original_org_id]
                else:
                    try:
                        org_url = org_data_json.get("url") if org_data_json.get("url") else None
                        org_to_insert = OrganisationDB(
                            id=original_org_id, name=org_data_json.get("name", "Unknown Organisation"),
                            description=org_data_json.get("description"), url=org_url, # HttpUrl is fine here
                            contact_phone=org_data_json.get("contact_phone")
                        )
                        cursor.execute(
                            """
                            INSERT INTO organisations (id, name, description, url, contact_phone)
                            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;
                            """, # ON CONFLICT is PostgreSQL specific
                            (org_to_insert.id, org_to_insert.name, org_to_insert.description,
                             str(org_to_insert.url) if org_to_insert.url else None, # Convert HttpUrl to str for DB
                             org_to_insert.contact_phone)
                        )
                        db_org_id = org_to_insert.id
                        inserted_org_ids[original_org_id] = db_org_id
                    except Exception as e:
                        print(f"Error processing organisation for offer '{original_offer_id}': {e}")
                        conn.rollback(); continue
            else:
                print(f"Warning: Missing org data for offer '{original_offer_id}'. Skipping.")
                continue

            # 2. Location
            loc_data_json = item_data.get("location")
            db_loc_id = None
            if loc_data_json and isinstance(loc_data_json, dict):
                original_loc_id = loc_data_json.get("id")
                if not original_loc_id:
                    print(f"Warning: Loc data missing 'id' in offer '{original_offer_id}'. Skipping.")
                    continue
                if original_loc_id in inserted_loc_ids:
                    db_loc_id = inserted_loc_ids[original_loc_id]
                else:
                    try:
                        # LocationDB model expects lat/lon for data_handler to make geom
                        # but for migration, we make geom directly.
                        lat = loc_data_json.get("latitude")
                        lon = loc_data_json.get("longitude")
                        geom_sql = None
                        if lat is not None and lon is not None:
                            geom_sql = f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)"

                        # Accessibility is List[str], psycopg2 can handle list -> JSONB
                        accessibility_list = loc_data_json.get("accessibility", [])

                        cursor.execute(
                            f"""
                            INSERT INTO locations (id, name, address_1, city, postal_code, geom, accessibility)
                            VALUES (%s, %s, %s, %s, %s, {geom_sql if geom_sql else 'NULL'}, %s) ON CONFLICT (id) DO NOTHING;
                            """,
                            (original_loc_id, loc_data_json.get("name", "Unknown Location"),
                             loc_data_json.get("address_1"), loc_data_json.get("city"),
                             loc_data_json.get("postal_code"), json.dumps(accessibility_list)) # Pass list as JSON string for JSONB
                        )
                        db_loc_id = original_loc_id
                        inserted_loc_ids[original_loc_id] = db_loc_id
                    except Exception as e:
                        print(f"Error processing location for offer '{original_offer_id}': {e}")
                        conn.rollback(); continue
            else:
                print(f"Warning: Missing loc data for offer '{original_offer_id}'. Skipping.")
                continue

            if not db_org_id or not db_loc_id:
                print(f"Skipping offer '{original_offer_id}' due to missing org/loc DB ID.")
                continue

            # 3. Offer
            try:
                offer_url = item_data.get("url") if item_data.get("url") else None
                offer_to_insert = OfferDB( # Pydantic model for validation and structure
                    id=original_offer_id, service_id=item_data.get("service_id", str(uuid.uuid4())),
                    location_id=db_loc_id, organisation_id=db_org_id,
                    name=item_data.get("name", "Unnamed Offer"), description=item_data.get("description"),
                    url=offer_url, status=item_data.get("status", "active"), type=item_data.get("type", "unknown"),
                    in_person=item_data.get("in_person", False), remote=item_data.get("remote", False),
                    interpretation_services=item_data.get("interpretation_services", False),
                    phone_support=item_data.get("phone_support", False), online_support=item_data.get("online_support", False),
                    eligibility=item_data.get("eligibility")
                )

                # Prepare values for SQL, converting HttpUrl to string
                offer_values = (
                    offer_to_insert.id, offer_to_insert.service_id, offer_to_insert.location_id,
                    offer_to_insert.organisation_id, offer_to_insert.name, offer_to_insert.description,
                    str(offer_to_insert.url) if offer_to_insert.url else None, # Convert HttpUrl to str for DB
                    offer_to_insert.status, offer_to_insert.type,
                    offer_to_insert.in_person, offer_to_insert.remote, offer_to_insert.interpretation_services,
                    offer_to_insert.phone_support, offer_to_insert.online_support, offer_to_insert.eligibility
                )
                cursor.execute(
                    """
                    INSERT INTO offers (id, service_id, location_id, organisation_id, name, description, url,
                                        status, type, in_person, remote, interpretation_services,
                                        phone_support, online_support, eligibility)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING;
                    """,
                    offer_values
                )
            except Exception as e:
                print(f"Error processing main offer data for '{original_offer_id}': {e}")
                conn.rollback(); continue

            # 4. Cost Options
            cost_options_json = item_data.get("cost_options", [])
            for co_json in cost_options_json:
                try:
                    co_db = CostOptionDB(offer_id=original_offer_id, **co_json) # id auto-generated
                    cursor.execute(
                        "INSERT INTO cost_options (id, offer_id, amount, amount_description, option) VALUES (%s,%s,%s,%s,%s);",
                        (co_db.id, co_db.offer_id, co_db.amount, co_db.amount_description, co_db.option)
                    )
                except Exception as e:
                    print(f"Error processing cost_option for offer '{original_offer_id}': {e}")

            # 5. Service Schedules
            schedules_json = item_data.get("service_schedules", [])
            for sched_json in schedules_json:
                try:
                    opens_at = time.fromisoformat(sched_json["opens_at"]) if sched_json.get("opens_at") else None
                    closes_at = time.fromisoformat(sched_json["closes_at"]) if sched_json.get("closes_at") else None
                    valid_from = date.fromisoformat(sched_json["valid_from"]) if sched_json.get("valid_from") else None
                    valid_to = date.fromisoformat(sched_json["valid_to"]) if sched_json.get("valid_to") else None
                    weekdays_list = sched_json.get("valid_for_weekdays", [])

                    sched_db = ServiceScheduleDB( # id auto-generated
                        offer_id=original_offer_id, opens_at=opens_at, closes_at=closes_at,
                        valid_from=valid_from, valid_to=valid_to,
                        valid_for_weekdays=weekdays_list, # Model expects list, psycopg2 handles JSONB
                        description=sched_json.get("description")
                    )
                    cursor.execute(
                        """
                        INSERT INTO service_schedules (id, offer_id, opens_at, closes_at, valid_from, valid_to,
                                                       valid_for_weekdays, description)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
                        """,
                        (sched_db.id, sched_db.offer_id, sched_db.opens_at, sched_db.closes_at,
                         sched_db.valid_from, sched_db.valid_to, json.dumps(sched_db.valid_for_weekdays), sched_db.description)
                    )
                except Exception as e:
                     print(f"Error processing service_schedule for offer '{original_offer_id}': {e}")

            # 6. Service Areas
            areas_json = item_data.get("service_areas", [])
            for area_json in areas_json:
                try:
                    area_db = ServiceAreaDB(offer_id=original_offer_id, **area_json) # id auto-generated
                    cursor.execute(
                        "INSERT INTO service_areas (id, offer_id, name) VALUES (%s,%s,%s);",
                        (area_db.id, area_db.offer_id, area_db.name)
                    )
                except Exception as e:
                    print(f"Error processing service_area for offer '{original_offer_id}': {e}")

            conn.commit()
            print(f"Successfully processed offer with original ID: {original_offer_id}")

        print("Data migration process completed.")

    except psycopg2.Error as e:
        print(f"A PostgreSQL error occurred: {e}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        print("PostgreSQL connection closed.")

if __name__ == "__main__":
    # Set up environment variables if running directly and not set elsewhere
    # For testing, ensure these are correctly pointing to your test DB
    os.environ.setdefault("PGDATABASE", "offers_db")
    os.environ.setdefault("PGUSER", "offer_user")
    os.environ.setdefault("PGPASSWORD", "offer_password")
    os.environ.setdefault("PGHOST", "localhost")
    os.environ.setdefault("PGPORT", "5432")

    DB_NAME = os.getenv("PGDATABASE") # Re-assign after setdefault
    DB_USER = os.getenv("PGUSER")
    DB_PASSWORD = os.getenv("PGPASSWORD")
    DB_HOST = os.getenv("PGHOST")
    DB_PORT = os.getenv("PGPORT")

    migrate_data_postgres()

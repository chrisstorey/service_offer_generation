import json
import sqlite3
import uuid
from typing import List, Dict, Any, Optional
from datetime import time, date

# Assuming models.py is in the same directory or accessible in PYTHONPATH
from models import (
    OrganisationDB, LocationDB, OfferDB, CostOptionDB, ServiceScheduleDB, ServiceAreaDB
)

SOURCE_JSON_FILE = "offers.json"
DATABASE_FILE = "offers.sqlite"

def convert_bool_to_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return 1 if value else 0
    return None # Or raise error, or return a default

def format_time_to_string(t: Optional[time]) -> Optional[str]:
    return t.isoformat() if t else None

def format_date_to_string(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def migrate_data():
    print(f"Starting migration from {SOURCE_JSON_FILE} to {DATABASE_FILE}...")

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
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print("Connected to SQLite database.")

        # Keep track of inserted organisations and locations to avoid duplicates by their original ID
        inserted_org_ids: Dict[str, str] = {} # Maps original JSON ID to DB ID (which might be the same)
        inserted_loc_ids: Dict[str, str] = {} # Maps original JSON ID to DB ID

        for item_data in raw_data:
            original_offer_id = item_data.get("id", str(uuid.uuid4())) # Use existing if available

            # 1. Organisation
            org_data_json = item_data.get("organisation")
            db_org_id = None
            if org_data_json and isinstance(org_data_json, dict):
                original_org_id = org_data_json.get("id")
                if not original_org_id:
                    print(f"Warning: Organisation data missing 'id' in offer '{original_offer_id}'. Skipping org.")
                elif original_org_id in inserted_org_ids:
                    db_org_id = inserted_org_ids[original_org_id]
                    # print(f"Organisation '{original_org_id}' already processed. Using DB ID: {db_org_id}")
                else:
                    try:
                        # Ensure URL is valid or None
                        org_url = org_data_json.get("url")
                        if org_url == "": org_url = None

                        org_to_insert = OrganisationDB(
                            id=original_org_id, # Use original ID as primary key
                            name=org_data_json.get("name", "Unknown Organisation"),
                            description=org_data_json.get("description"),
                            url=org_url,
                            contact_phone=org_data_json.get("contact_phone")
                        )
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO organisations (id, name, description, url, contact_phone)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (org_to_insert.id, org_to_insert.name, org_to_insert.description,
                             str(org_to_insert.url) if org_to_insert.url else None, org_to_insert.contact_phone)
                        )
                        db_org_id = org_to_insert.id
                        inserted_org_ids[original_org_id] = db_org_id
                        # print(f"Inserted/Found Organisation ID: {db_org_id} (Original: {original_org_id})")
                    except Exception as e: # Catch Pydantic validation or other errors
                        print(f"Error processing organisation for offer '{original_offer_id}': {e}. Data: {org_data_json}")
                        continue # Skip this offer if org processing fails critically
            else:
                print(f"Warning: Missing organisation data for offer '{original_offer_id}'.")
                continue # Offer requires an organisation

            # 2. Location
            loc_data_json = item_data.get("location")
            db_loc_id = None
            if loc_data_json and isinstance(loc_data_json, dict):
                original_loc_id = loc_data_json.get("id")
                if not original_loc_id:
                    print(f"Warning: Location data missing 'id' in offer '{original_offer_id}'. Skipping loc.")
                elif original_loc_id in inserted_loc_ids:
                    db_loc_id = inserted_loc_ids[original_loc_id]
                    # print(f"Location '{original_loc_id}' already processed. Using DB ID: {db_loc_id}")
                else:
                    try:
                        loc_to_insert = LocationDB(
                            id=original_loc_id, # Use original ID
                            name=loc_data_json.get("name", "Unknown Location"),
                            address_1=loc_data_json.get("address_1"),
                            city=loc_data_json.get("city"),
                            postal_code=loc_data_json.get("postal_code"),
                            latitude=loc_data_json.get("latitude"),
                            longitude=loc_data_json.get("longitude"),
                            accessibility=loc_data_json.get("accessibility", []) # Pydantic model will convert to JSON str
                        )
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO locations (id, name, address_1, city, postal_code, latitude, longitude, accessibility)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (loc_to_insert.id, loc_to_insert.name, loc_to_insert.address_1, loc_to_insert.city,
                             loc_to_insert.postal_code, loc_to_insert.latitude, loc_to_insert.longitude,
                             loc_to_insert.accessibility) # This is already a JSON string from Pydantic model
                        )
                        db_loc_id = loc_to_insert.id
                        inserted_loc_ids[original_loc_id] = db_loc_id
                        # print(f"Inserted/Found Location ID: {db_loc_id} (Original: {original_loc_id})")
                    except Exception as e:
                        print(f"Error processing location for offer '{original_offer_id}': {e}. Data: {loc_data_json}")
                        continue
            else:
                print(f"Warning: Missing location data for offer '{original_offer_id}'.")
                continue # Offer requires a location

            if not db_org_id or not db_loc_id:
                print(f"Skipping offer '{original_offer_id}' due to missing organisation or location DB ID.")
                continue

            # 3. Offer
            try:
                offer_url = item_data.get("url")
                if offer_url == "": offer_url = None

                offer_to_insert = OfferDB(
                    id=original_offer_id, # Use original ID
                    service_id=item_data.get("service_id", str(uuid.uuid4())),
                    location_id=db_loc_id,
                    organisation_id=db_org_id,
                    name=item_data.get("name", "Unnamed Offer"),
                    description=item_data.get("description"),
                    url=offer_url,
                    status=item_data.get("status", "active"),
                    type=item_data.get("type", "unknown"),
                    in_person=convert_bool_to_int(item_data.get("in_person", False)),
                    remote=convert_bool_to_int(item_data.get("remote", False)),
                    interpretation_services=convert_bool_to_int(item_data.get("interpretation_services", False)),
                    phone_support=convert_bool_to_int(item_data.get("phone_support", False)),
                    online_support=convert_bool_to_int(item_data.get("online_support", False)),
                    eligibility=item_data.get("eligibility")
                )
                cursor.execute(
                    """
                    INSERT INTO offers (id, service_id, location_id, organisation_id, name, description, url,
                                        status, type, in_person, remote, interpretation_services,
                                        phone_support, online_support, eligibility)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (offer_to_insert.id, offer_to_insert.service_id, offer_to_insert.location_id,
                     offer_to_insert.organisation_id, offer_to_insert.name, offer_to_insert.description,
                     str(offer_to_insert.url) if offer_to_insert.url else None, offer_to_insert.status, offer_to_insert.type,
                     offer_to_insert.in_person, offer_to_insert.remote, offer_to_insert.interpretation_services,
                     offer_to_insert.phone_support, offer_to_insert.online_support, offer_to_insert.eligibility)
                )
                # print(f"Inserted Offer ID: {offer_to_insert.id}")
            except Exception as e:
                print(f"Error processing main offer data for '{original_offer_id}': {e}. Data: {item_data}")
                continue # Skip to next offer if main data fails

            # 4. Cost Options
            cost_options_json = item_data.get("cost_options", [])
            for co_json in cost_options_json:
                try:
                    cost_option_to_insert = CostOptionDB(
                        offer_id=offer_to_insert.id, # Link to the offer
                        amount=co_json.get("amount", 0.0),
                        amount_description=co_json.get("amount_description"),
                        option=co_json.get("option", "N/A")
                    ) # id will be auto-generated by pydantic model
                    cursor.execute(
                        """
                        INSERT INTO cost_options (id, offer_id, amount, amount_description, option)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (cost_option_to_insert.id, cost_option_to_insert.offer_id, cost_option_to_insert.amount,
                         cost_option_to_insert.amount_description, cost_option_to_insert.option)
                    )
                except Exception as e:
                    print(f"Error processing cost_option for offer '{offer_to_insert.id}': {e}. Data: {co_json}")

            # 5. Service Schedules
            schedules_json = item_data.get("service_schedules", [])
            for sched_json in schedules_json:
                try:
                    # Convert time/date strings from JSON to Python objects then to ISO strings for DB
                    opens_at_time = time.fromisoformat(sched_json["opens_at"]) if sched_json.get("opens_at") else None
                    closes_at_time = time.fromisoformat(sched_json["closes_at"]) if sched_json.get("closes_at") else None
                    valid_from_date = date.fromisoformat(sched_json["valid_from"]) if sched_json.get("valid_from") else None
                    valid_to_date = date.fromisoformat(sched_json["valid_to"]) if sched_json.get("valid_to") else None

                    schedule_to_insert = ServiceScheduleDB(
                        offer_id=offer_to_insert.id,
                        opens_at=format_time_to_string(opens_at_time),
                        closes_at=format_time_to_string(closes_at_time),
                        valid_from=format_date_to_string(valid_from_date),
                        valid_to=format_date_to_string(valid_to_date),
                        valid_for_weekdays=sched_json.get("valid_for_weekdays", []), # Model handles JSON conversion
                        description=sched_json.get("description")
                    )
                    cursor.execute(
                        """
                        INSERT INTO service_schedules (id, offer_id, opens_at, closes_at, valid_from, valid_to,
                                                       valid_for_weekdays, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (schedule_to_insert.id, schedule_to_insert.offer_id, schedule_to_insert.opens_at,
                         schedule_to_insert.closes_at, schedule_to_insert.valid_from, schedule_to_insert.valid_to,
                         schedule_to_insert.valid_for_weekdays, schedule_to_insert.description)
                    )
                except Exception as e:
                     print(f"Error processing service_schedule for offer '{offer_to_insert.id}': {e}. Data: {sched_json}")

            # 6. Service Areas
            areas_json = item_data.get("service_areas", [])
            for area_json in areas_json:
                try:
                    area_to_insert = ServiceAreaDB(
                        offer_id=offer_to_insert.id,
                        name=area_json.get("name", "N/A")
                    )
                    cursor.execute(
                        """
                        INSERT INTO service_areas (id, offer_id, name)
                        VALUES (?, ?, ?)
                        """,
                        (area_to_insert.id, area_to_insert.offer_id, area_to_insert.name)
                    )
                except Exception as e:
                    print(f"Error processing service_area for offer '{offer_to_insert.id}': {e}. Data: {area_json}")

            conn.commit() # Commit after each full offer and its related entities are processed
            print(f"Successfully migrated offer with original ID: {original_offer_id} (DB ID: {offer_to_insert.id})")

        print("Data migration process completed.")

    except sqlite3.Error as e:
        print(f"An SQLite error occurred during migration: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # Potentially clear tables before migrating if this script is meant to be re-runnable for testing
    # For now, assumes tables are empty or `INSERT OR IGNORE` handles conflicts for orgs/locations.
    # Offers themselves are inserted directly; if an offer ID from JSON conflicts, it would error without OR IGNORE.
    # The current schema uses offer ID from JSON as primary key.
    migrate_data()

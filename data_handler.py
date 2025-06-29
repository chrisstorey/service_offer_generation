import psycopg2
import psycopg2.extras # For DictCursor
import uuid
import json
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import time, date

from models import (
    Offer, Organisation, Location,
    OfferCreateInput, OfferUpdateInput,
    OfferDB, OrganisationDB, LocationDB, # LocationDB now has lat/lon for input to this handler
    CostOptionDB, ServiceScheduleDB, ServiceAreaDB,
    CostOption, ServiceSchedule, ServiceArea
)

DB_NAME = os.getenv("PGDATABASE", "offers_db")
DB_USER = os.getenv("PGUSER", "offer_user")
DB_PASSWORD = os.getenv("PGPASSWORD", "offer_password")
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")

def get_db_connection() -> psycopg2.extensions.connection:
    """Establishes and returns a new PostgreSQL database connection."""
    conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
    conn = psycopg2.connect(conn_string)
    return conn

def _dict_row(cursor: psycopg2.extensions.cursor) -> Optional[Dict[str, Any]]:
    """Converts a fetched row to a dict if a row exists."""
    row = cursor.fetchone()
    if row:
        return {desc[0]: value for desc, value in zip(cursor.description, row)}
    return None

def _dict_rows(cursor: psycopg2.extensions.cursor) -> List[Dict[str, Any]]:
    """Converts all fetched rows to a list of dicts."""
    return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in cursor.fetchall()]


def _fetch_organisation(org_id: str, cursor: psycopg2.extensions.cursor) -> Optional[Organisation]:
    cursor.execute("SELECT * FROM organisations WHERE id = %s", (org_id,))
    row_dict = _dict_row(cursor)
    return Organisation(**row_dict) if row_dict else None

def _fetch_location(loc_id: str, cursor: psycopg2.extensions.cursor) -> Optional[Location]:
    # Retrieve ST_X(geom) as longitude, ST_Y(geom) as latitude
    cursor.execute(
        "SELECT id, name, address_1, city, postal_code, "
        "ST_X(geom) AS longitude, ST_Y(geom) AS latitude, accessibility "
        "FROM locations WHERE id = %s", (loc_id,)
    )
    row_dict = _dict_row(cursor)
    if not row_dict:
        return None

    # accessibility is JSONB, psycopg2 should convert it to a Python list automatically.
    # If it's a string, it means it wasn't properly inserted as JSONB or auto-conversion isn't happening.
    # Models.py Location expects accessibility to be List[str].
    if isinstance(row_dict.get('accessibility'), str): # Should ideally be list from JSONB
        try:
            row_dict['accessibility'] = json.loads(row_dict['accessibility'])
        except json.JSONDecodeError:
            row_dict['accessibility'] = []

    return Location(**row_dict)


def _fetch_cost_options(offer_id: str, cursor: psycopg2.extensions.cursor) -> List[CostOption]:
    cursor.execute("SELECT amount, amount_description, option FROM cost_options WHERE offer_id = %s", (offer_id,))
    return [CostOption(**row_dict) for row_dict in _dict_rows(cursor)]

def _fetch_service_schedules(offer_id: str, cursor: psycopg2.extensions.cursor) -> List[ServiceSchedule]:
    cursor.execute("SELECT opens_at, closes_at, valid_from, valid_to, valid_for_weekdays, description FROM service_schedules WHERE offer_id = %s", (offer_id,))
    schedules_data = _dict_rows(cursor)
    # valid_for_weekdays is JSONB, psycopg2 should convert to list.
    # opens_at, closes_at are TIME, psycopg2 converts to datetime.time.
    # valid_from, valid_to are DATE, psycopg2 converts to datetime.date.
    return [ServiceSchedule(**s) for s in schedules_data]


def _fetch_service_areas(offer_id: str, cursor: psycopg2.extensions.cursor) -> List[ServiceArea]:
    cursor.execute("SELECT name FROM service_areas WHERE offer_id = %s", (offer_id,))
    return [ServiceArea(**row_dict) for row_dict in _dict_rows(cursor)]

def _construct_offer_from_db_data(offer_db_data: Dict[str, Any], cursor: psycopg2.extensions.cursor) -> Offer:
    offer_id = offer_db_data["id"]

    org = _fetch_organisation(offer_db_data["organisation_id"], cursor)
    loc = _fetch_location(offer_db_data["location_id"], cursor)

    if not org or not loc:
        raise ValueError(f"Organisation or Location not found for offer {offer_id}")

    # Boolean fields are directly handled by psycopg2
    return Offer(
        **offer_db_data, # Pass the dict directly
        organisation=org,
        location=loc,
        cost_options=_fetch_cost_options(offer_id, cursor),
        service_schedules=_fetch_service_schedules(offer_id, cursor),
        service_areas=_fetch_service_areas(offer_id, cursor)
    )

def load_offers(
    service_type: Optional[str] = None,
    city: Optional[str] = None,
    in_person: Optional[bool] = None,
    remote: Optional[bool] = None,
    organisation_name: Optional[str] = None,
    # PostGIS specific filters (example)
    current_lat: Optional[float] = None,
    current_lon: Optional[float] = None,
    radius_km: Optional[float] = None
) -> List[Offer]:
    conn = get_db_connection()
    cursor = conn.cursor()

    query_parts = ["SELECT o.* FROM offers o"]
    joins = [
        "LEFT JOIN locations l ON o.location_id = l.id",
        "LEFT JOIN organisations org ON o.organisation_id = org.id"
    ]
    conditions = ["1=1"]
    params: List[Any] = []

    if service_type:
        conditions.append("o.type ILIKE %s") # ILIKE for case-insensitive
        params.append(f"%{service_type}%")
    if city:
        conditions.append("l.city ILIKE %s")
        params.append(f"%{city}%")
    if in_person is not None:
        conditions.append("o.in_person = %s")
        params.append(in_person)
    if remote is not None:
        conditions.append("o.remote = %s")
        params.append(remote)
    if organisation_name:
        conditions.append("org.name ILIKE %s")
        params.append(f"%{organisation_name}%")

    if current_lat is not None and current_lon is not None and radius_km is not None:
        # Ensure PostGIS is enabled and l.geom exists for this to work
        # ST_DWithin uses meters for geometry, or degrees for geography.
        # Assuming geom is GEOMETRY(Point, 4326) (degrees), radius needs conversion or use geography.
        # For simplicity, let's assume we might use ST_DistanceSphere for direct degree comparison if geom is Point.
        # Or, more robustly, cast to geography for ST_DWithin in meters.
        # ST_DWithin(geography(l.geom), ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        # This example uses a simpler form, assuming l.geom is geography or a cast will work.
        # Note: Proper spatial queries can be complex and depend on exact column types and indexing.
        conditions.append("ST_DWithin(l.geom::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)")
        params.extend([current_lon, current_lat, radius_km * 1000]) # radius in meters


    final_query = " ".join(query_parts + joins) + " WHERE " + " AND ".join(conditions) + " ORDER BY o.name;"

    cursor.execute(final_query, tuple(params))
    offer_rows_dicts = _dict_rows(cursor)

    offers = [_construct_offer_from_db_data(row_dict, cursor) for row_dict in offer_rows_dicts]

    conn.close()
    return offers

def get_offer_by_id(offer_id: str) -> Optional[Offer]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM offers WHERE id = %s", (offer_id,))
    row_dict = _dict_row(cursor)

    offer = None
    if row_dict:
        offer = _construct_offer_from_db_data(row_dict, cursor)

    conn.close()
    return offer

def add_offer(offer_data: OfferCreateInput) -> Offer:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        db_org_id: Optional[str] = offer_data.organisation_id
        if not db_org_id and offer_data.new_organisation:
            org_db = offer_data.new_organisation # This is OrganisationDB
            if not org_db.id: org_db.id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO organisations (id, name, description, url, contact_phone) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (org_db.id, org_db.name, org_db.description, str(org_db.url) if org_db.url else None, org_db.contact_phone)
            )
            db_org_id = cursor.fetchone()[0]
        elif not db_org_id:
             raise ValueError("Organisation ID or new Organisation data must be provided.")

        db_loc_id: Optional[str] = offer_data.location_id
        if not db_loc_id:
            if offer_data.new_location_name and offer_data.new_location_latitude is not None and offer_data.new_location_longitude is not None:
                loc_id_to_insert = str(uuid.uuid4())
                # psycopg2 can handle list for JSONB if new_location_accessibility is List[str]
                # The model OfferCreateInput defines new_location_accessibility as List[str]
                accessibility_jsonb = json.dumps(offer_data.new_location_accessibility)

                cursor.execute(
                    "INSERT INTO locations (id, name, address_1, city, postal_code, geom, accessibility) "
                    "VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s) RETURNING id;",
                    (loc_id_to_insert, offer_data.new_location_name, offer_data.new_location_address_1,
                     offer_data.new_location_city, offer_data.new_location_postal_code,
                     offer_data.new_location_longitude, offer_data.new_location_latitude, # lon, lat for ST_MakePoint
                     accessibility_jsonb)
                )
                db_loc_id = cursor.fetchone()[0]
            else:
                raise ValueError("Location ID or new Location data (name, lat, lon) must be provided.")

        new_offer_db_id = str(uuid.uuid4())
        offer_db_vals = (
            new_offer_db_id, offer_data.service_id, db_loc_id, db_org_id, offer_data.name,
            offer_data.description, str(offer_data.url) if offer_data.url else None,
            offer_data.status, offer_data.type, offer_data.in_person, offer_data.remote,
            offer_data.interpretation_services, offer_data.phone_support, offer_data.online_support,
            offer_data.eligibility
        )
        cursor.execute(
            "INSERT INTO offers (id, service_id, location_id, organisation_id, name, description, url, "
            "status, type, in_person, remote, interpretation_services, phone_support, online_support, eligibility) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",
            offer_db_vals
        )

        for co in offer_data.cost_options:
            co_db = CostOptionDB(offer_id=new_offer_db_id, **co.model_dump())
            cursor.execute("INSERT INTO cost_options (id, offer_id, amount, amount_description, option) VALUES (%s,%s,%s,%s,%s);",
                           (co_db.id, co_db.offer_id, co_db.amount, co_db.amount_description, co_db.option))

        for sched in offer_data.service_schedules:
            sched_db = ServiceScheduleDB(offer_id=new_offer_db_id, **sched.model_dump())
            cursor.execute(
                "INSERT INTO service_schedules (id, offer_id, opens_at, closes_at, valid_from, valid_to, valid_for_weekdays, description) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s);",
                (sched_db.id, sched_db.offer_id, sched_db.opens_at, sched_db.closes_at, sched_db.valid_from,
                 sched_db.valid_to, json.dumps(sched_db.valid_for_weekdays), sched_db.description) # weekdays as JSONB
            )

        for area in offer_data.service_areas:
            area_db = ServiceAreaDB(offer_id=new_offer_db_id, **area.model_dump())
            cursor.execute("INSERT INTO service_areas (id, offer_id, name) VALUES (%s,%s,%s);",
                           (area_db.id, area_db.offer_id, area_db.name))
        conn.commit()

        cursor.execute("SELECT * FROM offers WHERE id = %s", (new_offer_db_id,))
        new_offer_row_dict = _dict_row(cursor)
        if not new_offer_row_dict: raise Exception("Failed to retrieve newly added offer.")

        return _construct_offer_from_db_data(new_offer_row_dict, cursor)

    except (psycopg2.Error, ValueError, Exception) as e:
        if conn: conn.rollback()
        raise ValueError(f"Database error adding offer: {e}") from e
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def update_offer(offer_id: str, offer_data: OfferUpdateInput) -> Optional[Offer]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT organisation_id, location_id FROM offers WHERE id = %s", (offer_id,))
        existing_refs = _dict_row(cursor)
        if not existing_refs: return None

        current_org_id = offer_data.organisation_id if offer_data.organisation_id else existing_refs['organisation_id']
        current_loc_id = offer_data.location_id if offer_data.location_id else existing_refs['location_id']

        if offer_data.new_organisation and not offer_data.organisation_id : # Create new org if full data given AND no ID
            org_db = offer_data.new_organisation
            if not org_db.id: org_db.id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO organisations (id, name, description, url, contact_phone) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description, url=EXCLUDED.url, contact_phone=EXCLUDED.contact_phone RETURNING id;",
                (org_db.id, org_db.name, org_db.description, str(org_db.url) if org_db.url else None, org_db.contact_phone)
            )
            current_org_id = cursor.fetchone()[0]

        if offer_data.new_location_name and offer_data.new_location_latitude is not None and \
           offer_data.new_location_longitude is not None and not offer_data.location_id:
            loc_id_to_use = str(uuid.uuid4())
            accessibility_jsonb = json.dumps(offer_data.new_location_accessibility or [])
            cursor.execute(
                "INSERT INTO locations (id, name, address_1, city, postal_code, geom, accessibility) "
                "VALUES (%s,%s,%s,%s,%s, ST_SetSRID(ST_MakePoint(%s,%s),4326), %s) "
                "ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, address_1=EXCLUDED.address_1, city=EXCLUDED.city, postal_code=EXCLUDED.postal_code, geom=EXCLUDED.geom, accessibility=EXCLUDED.accessibility RETURNING id;",
                (loc_id_to_use, offer_data.new_location_name, offer_data.new_location_address_1, offer_data.new_location_city,
                 offer_data.new_location_postal_code, offer_data.new_location_longitude, offer_data.new_location_latitude,
                 accessibility_jsonb)
            )
            current_loc_id = cursor.fetchone()[0]

        # Build SET clause for offers table
        update_dict = offer_data.model_dump(exclude_unset=True, exclude={'organisation_id', 'new_organisation', 'location_id',
                                                                      'new_location_name', 'new_location_address_1',
                                                                      'new_location_city', 'new_location_postal_code',
                                                                      'new_location_latitude', 'new_location_longitude',
                                                                      'new_location_accessibility',
                                                                      'cost_options', 'service_schedules', 'service_areas'})
        update_dict['organisation_id'] = current_org_id
        update_dict['location_id'] = current_loc_id

        if update_dict: # Only update if there are fields to update
            set_clauses = [f"{key} = %s" for key in update_dict.keys()]
            params = list(update_dict.values()) + [offer_id]
            cursor.execute(f"UPDATE offers SET {', '.join(set_clauses)} WHERE id = %s", tuple(params))

        # Update related list-like items (delete all then re-insert)
        if offer_data.cost_options is not None:
            cursor.execute("DELETE FROM cost_options WHERE offer_id = %s", (offer_id,))
            for co in offer_data.cost_options:
                co_db = CostOptionDB(offer_id=offer_id, **co.model_dump())
                cursor.execute("INSERT INTO cost_options (id,offer_id,amount,amount_description,option) VALUES (%s,%s,%s,%s,%s);", tuple(co_db.model_dump().values()))

        if offer_data.service_schedules is not None:
            cursor.execute("DELETE FROM service_schedules WHERE offer_id = %s", (offer_id,))
            for sched in offer_data.service_schedules:
                sched_db = ServiceScheduleDB(offer_id=offer_id, **sched.model_dump())
                cursor.execute("INSERT INTO service_schedules (id,offer_id,opens_at,closes_at,valid_from,valid_to,valid_for_weekdays,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);",
                               (sched_db.id, sched_db.offer_id, sched_db.opens_at, sched_db.closes_at, sched_db.valid_from, sched_db.valid_to, json.dumps(sched_db.valid_for_weekdays), sched_db.description))

        if offer_data.service_areas is not None:
            cursor.execute("DELETE FROM service_areas WHERE offer_id = %s", (offer_id,))
            for area in offer_data.service_areas:
                area_db = ServiceAreaDB(offer_id=offer_id, **area.model_dump())
                cursor.execute("INSERT INTO service_areas (id,offer_id,name) VALUES (%s,%s,%s);", tuple(area_db.model_dump().values()))

        conn.commit()

        cursor.execute("SELECT * FROM offers WHERE id = %s", (offer_id,))
        updated_offer_row_dict = _dict_row(cursor)
        if not updated_offer_row_dict: return None
        return _construct_offer_from_db_data(updated_offer_row_dict, cursor)

    except (psycopg2.Error, ValueError, Exception) as e:
        if conn: conn.rollback()
        raise ValueError(f"Database error updating offer {offer_id}: {e}") from e
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def delete_offer(offer_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM offers WHERE id = %s", (offer_id,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error as e:
        if conn: conn.rollback()
        print(f"Database error deleting offer {offer_id}: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_distinct_cities() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM locations WHERE city IS NOT NULL ORDER BY city")
    cities = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cities

def get_distinct_service_types() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM offers WHERE type IS NOT NULL ORDER BY type")
    service_types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return service_types

def get_distinct_organisation_names() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM organisations WHERE name IS NOT NULL ORDER BY name")
    org_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return org_names

def get_all_organisations() -> List[Organisation]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organisations ORDER BY name")
    orgs = [Organisation(**row_dict) for row_dict in _dict_rows(cursor)]
    conn.close()
    return orgs

def get_all_locations() -> List[Location]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, address_1, city, postal_code, "
        "ST_X(geom) AS longitude, ST_Y(geom) AS latitude, accessibility "
        "FROM locations ORDER BY name"
    )

    locations_app_models = []
    for row_dict in _dict_rows(cursor):
        # accessibility should be a list from JSONB
        if isinstance(row_dict.get('accessibility'), str): # Should not happen if JSONB used correctly
            try:
                row_dict['accessibility'] = json.loads(row_dict['accessibility'])
            except json.JSONDecodeError:
                 row_dict['accessibility'] = []
        locations_app_models.append(Location(**row_dict))

    conn.close()
    return locations_app_models

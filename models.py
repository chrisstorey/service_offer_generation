from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator, ConfigDict, validator
from typing import List, Optional, Union, Any, Dict
import uuid
from datetime import date, time
import json # Still useful for JSONB if not using native list-to-JSONB psycopg2 feature directly in model
import sqlite3 # Keep for now, though might remove if fully PG

# --- Database Table Models (for PostgreSQL/PostGIS) ---

class LocationDB(BaseModel): # Represents structure for data going into/from DB
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address_1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    # geom: str  # Expected to be WKT string for PostGIS point e.g., "SRID=4326;POINT(lon lat)"
                # Or, for insertion, data_handler will create it. For retrieval, ST_AsGeoJSON or ST_AsText
    # For simplicity in Pydantic model, we might not store raw geom string here,
    # but handle it in data_handler. Let's keep lat/lon for input to data_handler,
    # which then constructs the geom.
    latitude: Optional[float] = None # Kept for input, will be used to create geom
    longitude: Optional[float] = None # Kept for input, will be used to create geom

    accessibility: List[str] = Field(default_factory=list) # Stored as JSONB in PG

    model_config = ConfigDict(from_attributes=True)

class OrganisationDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None # Pydantic will validate, store as TEXT
    contact_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class OfferDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    location_id: str   # Foreign Key to locations table
    organisation_id: str # Foreign Key to organisations table
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None # Store as TEXT
    status: str = "active"
    type: str
    in_person: bool = False # Stored as BOOLEAN in PG
    remote: bool = False
    interpretation_services: bool = False
    phone_support: bool = False
    online_support: bool = False
    eligibility: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CostOptionDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    offer_id: str
    amount: float
    amount_description: Optional[str] = None
    option: str

    model_config = ConfigDict(from_attributes=True)

class ServiceScheduleDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    offer_id: str
    opens_at: Optional[time] = None # Stored as TIME in PG
    closes_at: Optional[time] = None # Stored as TIME in PG
    valid_from: Optional[date] = None # Stored as DATE in PG
    valid_to: Optional[date] = None   # Stored as DATE in PG
    valid_for_weekdays: List[str] = Field(default_factory=list) # Stored as JSONB or TEXT[] in PG
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ServiceAreaDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    offer_id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


# --- Application Layer Models ---

class Location(BaseModel):
    id: str
    name: str
    address_1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None # For API input/output
    longitude: Optional[float] = None# For API input/output
    accessibility: List[str] = Field(default_factory=list)
    # geom_geojson: Optional[str] = None # Could be added if ST_AsGeoJSON is used

    model_config = ConfigDict(from_attributes=True)


class Organisation(OrganisationDB): # Can be same as DB if no transformations needed
    pass

class CostOption(BaseModel):
    amount: float
    amount_description: Optional[str] = None
    option: str

class ServiceSchedule(BaseModel):
    opens_at: Optional[time] = None
    closes_at: Optional[time] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    valid_for_weekdays: List[str] = Field(default_factory=list)
    description: Optional[str] = None

class ServiceArea(BaseModel):
    name: str

class Offer(BaseModel):
    id: str
    service_id: str
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    status: str = "active"
    type: str
    in_person: bool = False
    remote: bool = False
    interpretation_services: bool = False
    phone_support: bool = False
    online_support: bool = False
    eligibility: Optional[str] = None

    organisation: Organisation
    location: Location

    cost_options: List[CostOption] = Field(default_factory=list)
    service_areas: List[ServiceArea] = Field(default_factory=list)
    service_schedules: List[ServiceSchedule] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Models for creating and updating offers via API/Forms
class OfferCreateInput(BaseModel):
    service_id: str
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    status: str = "active"
    type: str
    in_person: bool = False
    remote: bool = False
    interpretation_services: bool = False
    phone_support: bool = False
    online_support: bool = False
    eligibility: Optional[str] = None

    organisation_id: Optional[str] = None
    new_organisation: Optional[OrganisationDB] = None

    location_id: Optional[str] = None
    # For new locations, expect lat/lon, data_handler will make geom
    new_location_name: Optional[str] = None
    new_location_address_1: Optional[str] = None
    new_location_city: Optional[str] = None
    new_location_postal_code: Optional[str] = None
    new_location_latitude: Optional[float] = None
    new_location_longitude: Optional[float] = None
    new_location_accessibility: List[str] = Field(default_factory=list)


    cost_options: List[CostOption] = Field(default_factory=list)
    service_areas: List[ServiceArea] = Field(default_factory=list)
    service_schedules: List[ServiceSchedule] = Field(default_factory=list)

class OfferUpdateInput(OfferCreateInput):
    service_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    in_person: Optional[bool] = None
    remote: Optional[bool] = None
    interpretation_services: Optional[bool] = None
    phone_support: Optional[bool] = None
    online_support: Optional[bool] = None

    new_organisation: Optional[OrganisationDB] = None

    new_location_name: Optional[str] = None
    new_location_address_1: Optional[str] = None
    new_location_city: Optional[str] = None
    new_location_postal_code: Optional[str] = None
    new_location_latitude: Optional[float] = None
    new_location_longitude: Optional[float] = None
    new_location_accessibility: Optional[List[str]] = None

    cost_options: Optional[List[CostOption]] = None
    service_areas: Optional[List[ServiceArea]] = None
    service_schedules: Optional[List[ServiceSchedule]] = None


class OfferFilterParams(BaseModel):
    type: Optional[str] = None
    city: Optional[str] = None
    in_person: Optional[bool] = None
    remote: Optional[bool] = None
    organisation_name: Optional[str] = None
    # For PostGIS, could add:
    # current_lat: Optional[float] = None
    # current_lon: Optional[float] = None
    # radius_km: Optional[float] = None


SQL_SCHEMA_POSTGIS = """
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE organisations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT, -- Store HttpUrl as TEXT
    contact_phone TEXT
);

CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address_1 TEXT,
    city TEXT,
    postal_code TEXT,
    -- latitude & longitude are not stored directly, but used to populate geom
    geom GEOMETRY(Point, 4326), -- SRID 4326 for WGS 84 lat/lon
    accessibility JSONB -- Store list as JSONB array
);
CREATE INDEX IF NOT EXISTS locations_geom_idx ON locations USING GIST (geom);

CREATE TABLE offers (
    id TEXT PRIMARY KEY,
    service_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    organisation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT, -- Store HttpUrl as TEXT
    status TEXT DEFAULT 'active',
    type TEXT NOT NULL,
    in_person BOOLEAN DEFAULT FALSE,
    remote BOOLEAN DEFAULT FALSE,
    interpretation_services BOOLEAN DEFAULT FALSE,
    phone_support BOOLEAN DEFAULT FALSE,
    online_support BOOLEAN DEFAULT FALSE,
    eligibility TEXT,
    FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE CASCADE,
    FOREIGN KEY (organisation_id) REFERENCES organisations (id) ON DELETE CASCADE
);

CREATE TABLE cost_options (
    id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    amount REAL NOT NULL, -- REAL for float
    amount_description TEXT,
    option TEXT NOT NULL,
    FOREIGN KEY (offer_id) REFERENCES offers (id) ON DELETE CASCADE
);

CREATE TABLE service_schedules (
    id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    opens_at TIME,
    closes_at TIME,
    valid_from DATE,
    valid_to DATE,
    valid_for_weekdays JSONB, -- Store list of strings as JSONB array
    description TEXT,
    FOREIGN KEY (offer_id) REFERENCES offers (id) ON DELETE CASCADE
);

CREATE TABLE service_areas (
    id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (offer_id) REFERENCES offers (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_offers_location_id ON offers (location_id);
CREATE INDEX IF NOT EXISTS idx_offers_organisation_id ON offers (organisation_id);
CREATE INDEX IF NOT EXISTS idx_offers_type ON offers (type);
CREATE INDEX IF NOT EXISTS idx_locations_city ON locations (city);
CREATE INDEX IF NOT EXISTS idx_organisations_name ON organisations (name);
"""

def get_sql_schema() -> str: # Renamed for clarity if old one is still around
    return SQL_SCHEMA_POSTGIS

# Remove old SQLite schema if it exists from previous version of this file
_SQLITE_SCHEMA_DEF_NAME = "SQL_SCHEMA"
if _SQLITE_SCHEMA_DEF_NAME in globals():
    del globals()[_SQLITE_SCHEMA_DEF_NAME]

"""
Summary of PostGIS-related changes:
1.  `LocationDB`: Removed `latitude`, `longitude`. `geom` will be handled by `data_handler.py` using PostGIS functions. `accessibility` changed to `List[str]` (for JSONB).
    (Note: For Pydantic `LocationDB` to be fully representative, `geom` could be `str` for WKT or a custom type. For now, `latitude`/`longitude` are kept on `LocationDB` to simplify data flow from `OfferCreateInput` to `data_handler` which then constructs the `geom`.)
    Re-correction: `LocationDB` will keep `latitude` and `longitude` for input convenience to `data_handler`. The actual `geom` column is in the SQL DDL.
2.  `Location` (App Model): Keeps `latitude`, `longitude` for API use. `accessibility` is `List[str]`.
3.  `ServiceScheduleDB`: `opens_at`/`closes_at` are `Optional[time]`, `valid_from`/`valid_to` are `Optional[date]`. `valid_for_weekdays` is `List[str]` (for JSONB).
4.  Boolean fields in `OfferDB` are `bool` (PostgreSQL `BOOLEAN`).
5.  `SQL_SCHEMA_POSTGIS`: Updated DDL for PostgreSQL/PostGIS:
    *   `CREATE EXTENSION IF NOT EXISTS postgis;`
    *   `locations.geom` is `GEOMETRY(Point, 4326)`.
    *   Spatial index `locations_geom_idx` added.
    *   `accessibility` and `valid_for_weekdays` use `JSONB`.
    *   `in_person` etc. in `offers` table use `BOOLEAN`.
    *   Date/Time fields in `service_schedules` use `DATE`/`TIME`.
6.  `OfferCreateInput`: Adjusted `new_location_accessibility` to be `List[str]`. `new_location` fields now directly feed into `LocationDB` which expects lat/lon.
7.  Removed `sqlite3` import as it's not directly used by these Pydantic models for PG.
"""

if __name__ == "__main__":
    print("PostGIS Schema DDL:")
    print(get_sql_schema())

    # Example LocationDB (how data might look before going to data_handler for geom creation)
    loc_db_input = LocationDB(name="Test Location PG", latitude=10.0, longitude=20.0, accessibility=["wheelchair"])
    print(f"\nLocationDB input example: {loc_db_input.model_dump_json(indent=2)}")

    # Example ServiceScheduleDB (psycopg2 will handle date/time/list to PG types)
    schedule_db_input = ServiceScheduleDB(
        offer_id="offer1",
        opens_at=time(9,0),
        valid_for_weekdays=["Monday", "Friday"]
    )
    print(f"\nServiceScheduleDB input example: {schedule_db_input.model_dump_json(indent=2)}")
    assert isinstance(schedule_db_input.opens_at, time)
    assert isinstance(schedule_db_input.valid_for_weekdays, list)

    print("\nModels seem OK for PostGIS schema.")

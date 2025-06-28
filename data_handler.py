import json
import os
import uuid
from typing import List, Optional, Dict, Any
from pydantic import ValidationError

from models import Offer, OfferCreate, OfferUpdate, Location, Organisation, LocationCreate, OrganisationCreate

OFFERS_FILE = "offers.json"
# For simplicity in this example, we'll assume organisations and locations data
# are primarily managed within the offers.json structure.
# A more robust system would have separate storage for them.

_offers_cache: List[Offer] = []
_organisations_cache: Dict[str, Organisation] = {}
_locations_cache: Dict[str, Location] = {}


def _load_data_from_json():
    """Loads offers, organisations, and locations from the JSON file into memory."""
    global _offers_cache, _organisations_cache, _locations_cache
    if not os.path.exists(OFFERS_FILE):
        _offers_cache = []
        _organisations_cache = {}
        _locations_cache = {}
        return

    try:
        with open(OFFERS_FILE, "r") as f:
            raw_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        _offers_cache = []
        _organisations_cache = {}
        _locations_cache = {}
        return

    temp_offers = []
    temp_orgs = {}
    temp_locs = {}

    for item_data in raw_data:
        try:
            # Extract and cache organisation
            org_data = item_data.get("organisation")
            if org_data and org_data.get("id"):
                if org_data["id"] not in temp_orgs:
                    org = Organisation(**org_data)
                    temp_orgs[org.id] = org

            # Extract and cache location
            loc_data = item_data.get("location")
            if loc_data and loc_data.get("id"):
                if loc_data["id"] not in temp_locs:
                    loc = Location(**loc_data)
                    temp_locs[loc.id] = loc

            # Create offer model instance
            # Ensure organisation and location are fully populated for the Offer model
            if org_data and loc_data:
                 # Create a copy to avoid modifying the original dict during iteration if necessary
                offer_model_data = item_data.copy()
                offer_model_data["organisation"] = temp_orgs.get(org_data["id"])
                offer_model_data["location"] = temp_locs.get(loc_data["id"])

                # Filter out None values for organisation and location if they weren't found
                # This should ideally not happen if data is consistent
                if offer_model_data["organisation"] and offer_model_data["location"]:
                    offer = Offer(**offer_model_data)
                    temp_offers.append(offer)
                else:
                    print(f"Warning: Skipping offer due to missing organisation/location data: {item_data.get('id')}")

        except ValidationError as e:
            print(f"Validation error loading item: {item_data.get('id', 'Unknown ID')}: {e}")
        except Exception as e:
            print(f"Generic error loading item: {item_data.get('id', 'Unknown ID')}: {e}")

    _offers_cache = temp_offers
    _organisations_cache = temp_orgs
    _locations_cache = temp_locs


def _save_data_to_json():
    """Saves the current state of offers (including their embedded orgs/locs) to the JSON file."""
    # We need to serialize the Offer models, which include nested Organisation and Location models.
    # Pydantic's model_dump(mode='json') or jsonable_encoder can be used.

    # FastAPI's jsonable_encoder is handy here if we were in a FastAPI context,
    # but Pydantic's model_dump works directly.

    serializable_offers = [offer.model_dump(mode="python") for offer in _offers_cache]

    with open(OFFERS_FILE, "w") as f:
        json.dump(serializable_offers, f, indent=2, default=str) # default=str for date/time


# Initial load of data when module is imported
_load_data_from_json()


def load_offers(
    service_type: Optional[str] = None,
    city: Optional[str] = None,
    in_person: Optional[bool] = None,
    remote: Optional[bool] = None,
    organisation_name: Optional[str] = None
) -> List[Offer]:
    """Loads all offers from the JSON file, with optional filtering."""
    if not _offers_cache: # Ensure data is loaded if cache is empty
        _load_data_from_json()

    filtered_offers = _offers_cache

    if service_type:
        filtered_offers = [o for o in filtered_offers if o.type and service_type.lower() in o.type.lower()]
    if city:
        filtered_offers = [o for o in filtered_offers if o.location and o.location.city and city.lower() in o.location.city.lower()]
    if in_person is not None:
        filtered_offers = [o for o in filtered_offers if o.in_person == in_person]
    if remote is not None:
        filtered_offers = [o for o in filtered_offers if o.remote == remote]
    if organisation_name:
        filtered_offers = [o for o in filtered_offers if o.organisation and o.organisation.name and organisation_name.lower() in o.organisation.name.lower()]

    return filtered_offers

def get_offer_by_id(offer_id: str) -> Optional[Offer]:
    """Retrieves a single offer by its ID."""
    if not _offers_cache:
        _load_data_from_json()
    for offer in _offers_cache:
        if offer.id == offer_id:
            return offer
    return None

def add_offer(offer_data: OfferCreate) -> Offer:
    """Adds a new offer to the list and saves to JSON."""
    global _offers_cache, _organisations_cache, _locations_cache

    # Handle Organisation
    org: Optional[Organisation] = None
    if offer_data.organisation_id and offer_data.organisation_id in _organisations_cache:
        org = _organisations_cache[offer_data.organisation_id]
    elif offer_data.organisation:
        # Create new organisation if full object is provided
        new_org_id = str(uuid.uuid4())
        org_create_data = offer_data.organisation.model_dump()
        org = Organisation(id=new_org_id, **org_create_data)
        _organisations_cache[new_org_id] = org
    if not org:
        raise ValueError("Organisation data is missing or invalid.")

    # Handle Location
    loc: Optional[Location] = None
    if offer_data.location_id and offer_data.location_id in _locations_cache:
        loc = _locations_cache[offer_data.location_id]
    elif offer_data.location:
        # Create new location if full object is provided
        new_loc_id = str(uuid.uuid4())
        loc_create_data = offer_data.location.model_dump()
        loc = Location(id=new_loc_id, **loc_create_data)
        _locations_cache[new_loc_id] = loc
    if not loc:
        raise ValueError("Location data is missing or invalid.")

    new_offer_id = str(uuid.uuid4())

    # Construct the full Offer model
    # Exclude 'organisation' and 'location' from OfferCreate as they are handled above
    offer_base_data = offer_data.model_dump(exclude={"organisation", "location", "organisation_id", "location_id"})

    new_offer = Offer(
        id=new_offer_id,
        **offer_base_data,
        organisation=org,
        location=loc
    )

    _offers_cache.append(new_offer)
    _save_data_to_json()
    return new_offer

def update_offer(offer_id: str, offer_data: OfferUpdate) -> Optional[Offer]:
    """Updates an existing offer by ID and saves to JSON."""
    global _offers_cache, _organisations_cache, _locations_cache
    offer_to_update = get_offer_by_id(offer_id)
    if not offer_to_update:
        return None

    update_data = offer_data.model_dump(exclude_unset=True)

    # Handle nested Organisation update/creation
    if "organisation" in update_data and isinstance(update_data["organisation"], dict):
        org_create_data = OrganisationCreate(**update_data.pop("organisation"))
        if offer_to_update.organisation: # Update existing
            updated_org_data = org_create_data.model_dump(exclude_unset=True)
            for key, value in updated_org_data.items():
                setattr(offer_to_update.organisation, key, value)
            _organisations_cache[offer_to_update.organisation.id] = offer_to_update.organisation
        else: # This case should ideally not happen if data is consistent
             raise ValueError("Cannot update non-existent organisation on offer.")
    elif "organisation_id" in update_data:
        org_id = update_data["organisation_id"]
        if org_id in _organisations_cache:
            offer_to_update.organisation = _organisations_cache[org_id]
        else:
            raise ValueError(f"Organisation with ID {org_id} not found.")


    # Handle nested Location update/creation
    if "location" in update_data and isinstance(update_data["location"], dict):
        loc_create_data = LocationCreate(**update_data.pop("location"))
        if offer_to_update.location: # Update existing
            updated_loc_data = loc_create_data.model_dump(exclude_unset=True)
            for key, value in updated_loc_data.items():
                setattr(offer_to_update.location, key, value)
            _locations_cache[offer_to_update.location.id] = offer_to_update.location
        else:
            raise ValueError("Cannot update non-existent location on offer.")
    elif "location_id" in update_data:
        loc_id = update_data["location_id"]
        if loc_id in _locations_cache:
            offer_to_update.location = _locations_cache[loc_id]
        else:
            raise ValueError(f"Location with ID {loc_id} not found.")


    # Update top-level fields
    for key, value in update_data.items():
        if hasattr(offer_to_update, key):
            # Handle complex types like lists of Pydantic models (e.g. cost_options)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                field_type = offer_to_update.__annotations__.get(key)
                # This is a simplification; proper list updates are more complex
                # For now, we replace the list.
                # E.g., if field_type is List[CostOption]
                # model_list = [CostOption(**item) for item in value]
                # setattr(offer_to_update, key, model_list)
                # For now, direct assignment if the structure matches:
                try:
                    if key == "cost_options":
                        offer_to_update.cost_options = [CostOption(**co) for co in value]
                    elif key == "service_areas":
                        offer_to_update.service_areas = [ServiceArea(**sa) for sa in value]
                    elif key == "service_schedules":
                         offer_to_update.service_schedules = [ServiceSchedule(**ss) for ss in value]
                    else:
                         setattr(offer_to_update, key, value)
                except ValidationError as e:
                    print(f"Validation error updating field {key}: {e}")
                    # Potentially skip this field or raise error
            else:
                setattr(offer_to_update, key, value)

    # Re-validate the whole model (optional, but good for consistency)
    try:
        Offer(**offer_to_update.model_dump())
    except ValidationError as e:
        print(f"Post-update validation failed for offer {offer_id}: {e}")
        # Potentially revert changes or handle error
        return None # Or raise error

    _save_data_to_json()
    return offer_to_update


def delete_offer(offer_id: str) -> bool:
    """Deletes an offer by its ID and saves to JSON."""
    global _offers_cache
    initial_len = len(_offers_cache)
    _offers_cache = [offer for offer in _offers_cache if offer.id != offer_id]
    if len(_offers_cache) < initial_len:
        _save_data_to_json()
        return True
    return False

def get_distinct_cities() -> List[str]:
    if not _offers_cache:
        _load_data_from_json()
    cities = set()
    for offer in _offers_cache:
        if offer.location and offer.location.city:
            cities.add(offer.location.city)
    return sorted(list(cities))

def get_distinct_service_types() -> List[str]:
    if not _offers_cache:
        _load_data_from_json()
    service_types = set()
    for offer in _offers_cache:
        if offer.type:
            service_types.add(offer.type)
    return sorted(list(service_types))

def get_distinct_organisation_names() -> List[str]:
    if not _offers_cache:
        _load_data_from_json()
    org_names = set()
    for offer in _offers_cache:
        if offer.organisation and offer.organisation.name:
            org_names.add(offer.organisation.name)
    return sorted(list(org_names))

# Helper to get all organisations and locations for dropdowns in forms
def get_all_organisations() -> List[Organisation]:
    if not _organisations_cache:
        _load_data_from_json()
    return list(_organisations_cache.values())

def get_all_locations() -> List[Location]:
    if not _locations_cache:
        _load_data_from_json()
    return list(_locations_cache.values())

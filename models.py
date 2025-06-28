from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Union
import uuid
from datetime import date, time

class LocationBase(BaseModel):
    name: str
    address_1: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accessibility: Optional[List[str]] = []

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: str

class OrganisationBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    contact_phone: Optional[str] = None

class OrganisationCreate(OrganisationBase):
    pass

class Organisation(OrganisationBase):
    id: str

class CostOption(BaseModel):
    amount: float
    amount_description: Optional[str] = None
    option: str

class ServiceSchedule(BaseModel):
    opens_at: Optional[time] = None
    closes_at: Optional[time] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    valid_for_weekdays: Optional[List[str]] = None
    description: Optional[str] = None

class ServiceArea(BaseModel):
    name: str

class OfferBase(BaseModel):
    service_id: str # Assuming this is pre-existing or generated elsewhere if it's a foreign key to a broader "services" catalog
    name: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    status: str = "active"
    type: str # e.g., vocational_training, education, financial_advice
    in_person: bool = False
    remote: bool = False
    interpretation_services: bool = False
    phone_support: bool = False
    online_support: bool = False
    cost_options: List[CostOption] = []
    eligibility: Optional[str] = None
    service_areas: List[ServiceArea] = []
    service_schedules: List[ServiceSchedule] = []

    # For creation/update, we might accept IDs for existing org/location
    # or allow creating new ones by passing the full object.
    # For simplicity now, let's assume we pass full objects or they are handled by ID in data_handler
    organisation_id: Optional[str] = None # To link to an existing Organisation
    location_id: Optional[str] = None # To link to an existing Location


class OfferCreate(OfferBase):
    # When creating, we might want to pass the full Organisation and Location objects
    # or just their IDs if they are expected to exist.
    # For now, let's allow passing full new objects if IDs are not provided.
    organisation: Optional[OrganisationCreate] = None
    location: Optional[LocationCreate] = None

    # Fields that will be in the final Offer model but not directly in OfferCreate
    # as they are derived or set by the system (like 'id')
    # or are expanded objects ('organisation', 'location' full models)

class OfferUpdate(OfferBase):
    # Similar to OfferCreate, but all fields are optional for partial updates
    service_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    in_person: Optional[bool] = None
    remote: Optional[bool] = None
    interpretation_services: Optional[bool] = None
    phone_support: Optional[bool] = None
    online_support: Optional[bool] = None
    cost_options: Optional[List[CostOption]] = None
    eligibility: Optional[str] = None
    service_areas: Optional[List[ServiceArea]] = None
    service_schedules: Optional[List[ServiceSchedule]] = None
    organisation_id: Optional[str] = None
    location_id: Optional[str] = None
    organisation: Optional[OrganisationCreate] = None # Allow updating/replacing org
    location: Optional[LocationCreate] = None # Allow updating/replacing loc


class Offer(OfferBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organisation: Organisation # Full embedded Organisation object
    location: Location       # Full embedded Location object

    model_config = {
        "from_attributes": True
    }

# Example of how a full Offer might look in the database (offers.json)
# This is just for reference, not part of the importable models.
# {
# "id": "518a29cd-3fc3-4f11-a111-1148ad6e49cd",
# "service_id": "9dba9b4a-9bea-453e-97e6-8f4814a330e0", -> OfferBase
# "location_id": "f96d0b7d-91b9-453f-b925-7d6a1130f27c", -> OfferBase (used to fetch Location)
# "organization_id": "3e85afdc-2957-4fe4-a5b5-63e11840cd73", -> OfferBase (used to fetch Organisation)
# "name": "Customer Service Skills Course - Huddersfield (Huddersfield Central Community Hub)", -> OfferBase
# "description": "Develops key customer service skills...", -> OfferBase
# "url": "https://www.kirkleesscouts.org.uk/", -> OfferBase
# "status": "active", -> OfferBase
# "type": "vocational_training", -> OfferBase
# "in_person": true, -> OfferBase
# "remote": false, -> OfferBase
# "interpretation_services": false, -> OfferBase
# "phone_support": true, -> OfferBase
# "online_support": true, -> OfferBase
# "cost_options": [...], -> OfferBase
# "eligibility": "Unemployed individuals residing in Huddersfield.", -> OfferBase
# "service_areas": [...], -> OfferBase
# "service_schedules": [...], -> OfferBase
# "organisation": { Organisation model data }, -> Offer (expanded)
# "location": { Location model data } -> Offer (expanded)
# }

# For filtering in the UI, we might want a separate model or just use query params.
# For now, query params directly mapped to Offer fields will be used.
class OfferFilterParams(BaseModel):
    type: Optional[str] = None
    city: Optional[str] = None # Will filter based on location.city
    in_person: Optional[bool] = None
    remote: Optional[bool] = None
    # Add more filterable fields as needed
    # service_area_name: Optional[str] = None # Filter by service_areas[0].name for simplicity
    # organisation_name: Optional[str] = None # Filter by organisation.name
    pass

from fastapi import FastAPI, Request, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.staticfiles import StaticFiles # Not currently used
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape
from datetime import time, date
import json
import uuid # For new org/loc IDs if not provided via form explicitly

from pydantic import ValidationError
from typing import List, Optional, Any

import models
import data_handler

app = FastAPI(title="Service Offers CRUD App with PostGIS")

# app.mount("/static", StaticFiles(directory="static"), name="static") # If you add static files

templates = Jinja2Templates(directory="templates")

def nl2br(value: Optional[str]) -> Markup:
    if value is None: return Markup("")
    return Markup(escape(value).replace('\n', '<br>\n'))

templates.env.filters['nl2br'] = nl2br
templates.env.globals['models'] = models
templates.env.globals['json'] = json # Make json available for dumping lists in forms

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse, name="list_offers_view")
async def list_offers_view(
    request: Request,
    service_type: Optional[str] = None,
    city: Optional[str] = None,
    in_person: Optional[bool] = None,
    remote: Optional[bool] = None,
    organisation_name: Optional[str] = None,
    # PostGIS specific query params (example)
    current_lat: Optional[float] = None,
    current_lon: Optional[float] = None,
    radius_km: Optional[float] = None
):
    offers = data_handler.load_offers(
        service_type=service_type, city=city, in_person=in_person, remote=remote,
        organisation_name=organisation_name,
        current_lat=current_lat, current_lon=current_lon, radius_km=radius_km
    )
    distinct_cities = data_handler.get_distinct_cities()
    distinct_service_types = data_handler.get_distinct_service_types()
    distinct_organisations = data_handler.get_distinct_organisation_names()

    return templates.TemplateResponse(
        "offers_list.html",
        {
            "request": request, "offers": offers,
            "distinct_cities": distinct_cities, "distinct_service_types": distinct_service_types,
            "distinct_organisations": distinct_organisations,
            "current_filters": {
                "service_type": service_type, "city": city, "in_person": in_person,
                "remote": remote, "organisation_name": organisation_name,
                "current_lat": current_lat, "current_lon": current_lon, "radius_km": radius_km
            }
        },
    )

@app.get("/offers/new", response_class=HTMLResponse, name="create_offer_form")
async def create_offer_form(request: Request):
    all_organisations = data_handler.get_all_organisations()
    all_locations = data_handler.get_all_locations()
    distinct_service_types = data_handler.get_distinct_service_types()
    return templates.TemplateResponse(
        "offer_form.html",
        {
            "request": request, "offer": None,
            "all_organisations": all_organisations, "all_locations": all_locations,
            "distinct_service_types": distinct_service_types,
            "form_action_url": app.url_path_for("create_offer_action")
        }
    )

def parse_form_schedule(
    schedule_description: Optional[str],
    schedule_opens_at_str: Optional[str],
    schedule_closes_at_str: Optional[str],
    schedule_valid_from_str: Optional[str],
    schedule_valid_to_str: Optional[str],
    schedule_weekdays_json_str: Optional[str]
) -> Optional[models.ServiceSchedule]:

    # Check if any schedule field has a meaningful value
    if not any(filter(None, [
        schedule_description, schedule_opens_at_str, schedule_closes_at_str,
        schedule_valid_from_str, schedule_valid_to_str,
        schedule_weekdays_json_str and schedule_weekdays_json_str != "[]" # Empty list string is not meaningful alone
    ])):
        return None

    weekdays_list: List[str] = []
    if schedule_weekdays_json_str:
        try:
            parsed_json = json.loads(schedule_weekdays_json_str)
            if isinstance(parsed_json, list):
                weekdays_list = [str(item) for item in parsed_json if isinstance(item, (str, int, float))] # Ensure items are strings
        except json.JSONDecodeError:
            pass # Keep weekdays_list empty

    return models.ServiceSchedule(
        description=schedule_description,
        opens_at=time.fromisoformat(schedule_opens_at_str) if schedule_opens_at_str else None,
        closes_at=time.fromisoformat(schedule_closes_at_str) if schedule_closes_at_str else None,
        valid_from=date.fromisoformat(schedule_valid_from_str) if schedule_valid_from_str else None,
        valid_to=date.fromisoformat(schedule_valid_to_str) if schedule_valid_to_str else None,
        valid_for_weekdays=weekdays_list
    )

@app.post("/offers", name="create_offer_action")
async def create_offer_action(request: Request,
    service_id: str = Form(...), name: str = Form(...), description: Optional[str] = Form(None),
    url: Optional[str] = Form(None), status: str = Form("active"), type: str = Form(...),
    in_person: bool = Form(False), remote: bool = Form(False),
    interpretation_services: bool = Form(False), phone_support: bool = Form(False),
    online_support: bool = Form(False), eligibility: Optional[str] = Form(None),
    organisation_id: Optional[str] = Form(None),
    new_organisation_name: Optional[str] = Form(None),
    new_organisation_description: Optional[str] = Form(None),
    new_organisation_url: Optional[str] = Form(None),
    new_organisation_contact_phone: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    new_location_name: Optional[str] = Form(None),
    new_location_address_1: Optional[str] = Form(None),
    new_location_city: Optional[str] = Form(None),
    new_location_postal_code: Optional[str] = Form(None),
    new_location_latitude: Optional[float] = Form(None),
    new_location_longitude: Optional[float] = Form(None),
    new_location_accessibility_json: Optional[str] = Form("[]"),
    cost_option_amount: Optional[float] = Form(None),
    cost_option_amount_description: Optional[str] = Form(None),
    cost_option_option: Optional[str] = Form(None),
    service_area_name: Optional[str] = Form(None),
    schedule_description: Optional[str] = Form(None),
    schedule_opens_at: Optional[str] = Form(None), schedule_closes_at: Optional[str] = Form(None),
    schedule_valid_from: Optional[str] = Form(None), schedule_valid_to: Optional[str] = Form(None),
    schedule_weekdays_json: Optional[str] = Form("[]")
):
    new_org_model_db: Optional[models.OrganisationDB] = None
    if new_organisation_name and not organisation_id:
        new_org_model_db = models.OrganisationDB(
            name=new_organisation_name, description=new_organisation_description,
            url=new_organisation_url or None, contact_phone=new_organisation_contact_phone
        )

    accessibility_list: List[str] = []
    if new_location_accessibility_json:
        try:
            parsed_json = json.loads(new_location_accessibility_json)
            if isinstance(parsed_json, list):
                accessibility_list = [str(item) for item in parsed_json if isinstance(item, (str, int, float))]
        except json.JSONDecodeError:
            pass # Keep accessibility_list empty

    cost_options_data = []
    if cost_option_amount is not None and cost_option_option:
        cost_options_data.append(models.CostOption(amount=cost_option_amount, amount_description=cost_option_amount_description, option=cost_option_option))

    service_areas_data = []
    if service_area_name:
        service_areas_data.append(models.ServiceArea(name=service_area_name))

    schedules_data = []
    parsed_schedule = parse_form_schedule(
        schedule_description, schedule_opens_at, schedule_closes_at,
        schedule_valid_from, schedule_valid_to, schedule_weekdays_json
    )
    if parsed_schedule: schedules_data.append(parsed_schedule)

    try:
        # OfferCreateInput now expects individual fields for new_location
        offer_create_input = models.OfferCreateInput(
            service_id=service_id, name=name, description=description, url=url or None,
            status=status, type=type, in_person=in_person, remote=remote,
            interpretation_services=interpretation_services, phone_support=phone_support,
            online_support=online_support, eligibility=eligibility,
            organisation_id=organisation_id, new_organisation=new_org_model_db,
            location_id=location_id,
            new_location_name=new_location_name if not location_id else None,
            new_location_address_1=new_location_address_1 if not location_id else None,
            new_location_city=new_location_city if not location_id else None,
            new_location_postal_code=new_location_postal_code if not location_id else None,
            new_location_latitude=new_location_latitude if not location_id else None,
            new_location_longitude=new_location_longitude if not location_id else None,
            new_location_accessibility=accessibility_list if not location_id and new_location_name else [],
            cost_options=cost_options_data, service_areas=service_areas_data,
            service_schedules=schedules_data
        )

        new_offer = data_handler.add_offer(offer_create_input)
        return RedirectResponse(url=app.url_path_for("offer_detail_view", offer_id=new_offer.id), status_code=status.HTTP_303_SEE_OTHER)

    except (ValidationError, ValueError) as e:
        error_detail = e.errors() if isinstance(e, ValidationError) else [{"msg": str(e), "loc": ["form"]}]
        # ... (error handling remains similar, pass data back to form) ...
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        distinct_service_types = data_handler.get_distinct_service_types()
        return templates.TemplateResponse("offer_form.html", {
            "request": request, "offer": None, "errors": error_detail, # Pass actual submitted values back for repopulation
            "all_organisations": all_organisations, "all_locations": all_locations,
            "distinct_service_types": distinct_service_types,
            "form_action_url": app.url_path_for("create_offer_action")
        }, status_code=422)


@app.get("/offers/{offer_id}", response_class=HTMLResponse, name="offer_detail_view")
async def offer_detail_view(request: Request, offer_id: str):
    offer = data_handler.get_offer_by_id(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return templates.TemplateResponse("offer_detail.html", {"request": request, "offer": offer})


@app.get("/offers/{offer_id}/edit", response_class=HTMLResponse, name="edit_offer_form")
async def edit_offer_form(request: Request, offer_id: str):
    offer = data_handler.get_offer_by_id(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    all_organisations = data_handler.get_all_organisations()
    all_locations = data_handler.get_all_locations()
    distinct_service_types = data_handler.get_distinct_service_types()

    offer_form_data = offer.model_dump()
    offer_form_data['organisation_id'] = offer.organisation.id
    offer_form_data['location_id'] = offer.location.id

    # For new_location_ fields, they are not typically part of an existing offer's data dump for edit
    # The form should provide fields for lat/lon if user wants to *change* location details,
    # or select a different existing location.
    # The current Location model has lat/lon, so these will be in offer_form_data['location']
    offer_form_data['new_location_latitude'] = offer.location.latitude
    offer_form_data['new_location_longitude'] = offer.location.longitude
    offer_form_data['new_location_accessibility_json'] = json.dumps(offer.location.accessibility or [])


    if offer.cost_options:
        co = offer.cost_options[0]
        offer_form_data.update({
            'cost_option_amount': co.amount,
            'cost_option_amount_description': co.amount_description,
            'cost_option_option': co.option
        })
    if offer.service_areas:
        offer_form_data['service_area_name'] = offer.service_areas[0].name
    if offer.service_schedules:
        sched = offer.service_schedules[0]
        offer_form_data.update({
            'schedule_description': sched.description,
            'schedule_opens_at': sched.opens_at.isoformat() if sched.opens_at else None,
            'schedule_closes_at': sched.closes_at.isoformat() if sched.closes_at else None,
            'schedule_valid_from': sched.valid_from.isoformat() if sched.valid_from else None,
            'schedule_valid_to': sched.valid_to.isoformat() if sched.valid_to else None,
            'schedule_weekdays_json': json.dumps(sched.valid_for_weekdays or [])
        })

    return templates.TemplateResponse(
        "offer_form.html",
        {
            "request": request, "offer": offer_form_data,
            "all_organisations": all_organisations, "all_locations": all_locations,
            "distinct_service_types": distinct_service_types,
            "form_action_url": app.url_path_for("edit_offer_action", offer_id=offer_id)
        }
    )

@app.post("/offers/{offer_id}/update", name="edit_offer_action")
async def edit_offer_action(request: Request, offer_id: str,
    # Similar to create, but new_org/loc fields are for changing to a *newly created* one
    service_id: str = Form(...), name: str = Form(...), description: Optional[str] = Form(None),
    url: Optional[str] = Form(None), status: str = Form(...), type: str = Form(...),
    in_person: bool = Form(False), remote: bool = Form(False),
    interpretation_services: bool = Form(False), phone_support: bool = Form(False),
    online_support: bool = Form(False), eligibility: Optional[str] = Form(None),
    organisation_id: Optional[str] = Form(None), # Can select a different existing org
    new_organisation_name: Optional[str] = Form(None), # Or create a new one to switch to
    new_organisation_description: Optional[str] = Form(None),
    new_organisation_url: Optional[str] = Form(None),
    new_organisation_contact_phone: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None), # Can select a different existing loc
    new_location_name: Optional[str] = Form(None), # Or create a new one
    new_location_address_1: Optional[str] = Form(None),
    new_location_city: Optional[str] = Form(None),
    new_location_postal_code: Optional[str] = Form(None),
    new_location_latitude: Optional[float] = Form(None),
    new_location_longitude: Optional[float] = Form(None),
    new_location_accessibility_json: Optional[str] = Form("[]"),
    cost_option_amount: Optional[float] = Form(None),
    cost_option_amount_description: Optional[str] = Form(None),
    cost_option_option: Optional[str] = Form(None),
    service_area_name: Optional[str] = Form(None),
    schedule_description: Optional[str] = Form(None),
    schedule_opens_at: Optional[str] = Form(None), schedule_closes_at: Optional[str] = Form(None),
    schedule_valid_from: Optional[str] = Form(None), schedule_valid_to: Optional[str] = Form(None),
    schedule_weekdays_json: Optional[str] = Form("[]")
):
    existing_offer_model = data_handler.get_offer_by_id(offer_id)
    if not existing_offer_model:
        raise HTTPException(status_code=404, detail="Offer not found to update")

    new_org_model_db: Optional[models.OrganisationDB] = None
    if new_organisation_name and not organisation_id: # If creating a new org to associate
        new_org_model_db = models.OrganisationDB(name=new_organisation_name, description=new_organisation_description, url=new_organisation_url or None, contact_phone=new_organisation_contact_phone)

    accessibility_list: List[str] = []
    if new_location_accessibility_json:
        try:
            parsed_json = json.loads(new_location_accessibility_json)
            if isinstance(parsed_json, list): accessibility_list = [str(item) for item in parsed_json if isinstance(item, (str, int, float))]
        except json.JSONDecodeError: pass

    cost_options_data = []
    if cost_option_amount is not None and cost_option_option:
        cost_options_data.append(models.CostOption(amount=cost_option_amount, amount_description=cost_option_amount_description, option=cost_option_option))

    service_areas_data = []
    if service_area_name:
        service_areas_data.append(models.ServiceArea(name=service_area_name))

    schedules_data = []
    parsed_schedule = parse_form_schedule(schedule_description, schedule_opens_at, schedule_closes_at, schedule_valid_from, schedule_valid_to, schedule_weekdays_json)
    if parsed_schedule: schedules_data.append(parsed_schedule)

    try:
        offer_update_input = models.OfferUpdateInput(
            service_id=service_id, name=name, description=description, url=url or None, status=status, type=type,
            in_person=in_person, remote=remote, interpretation_services=interpretation_services,
            phone_support=phone_support, online_support=online_support, eligibility=eligibility,
            organisation_id=organisation_id, new_organisation=new_org_model_db,
            location_id=location_id,
            new_location_name=new_location_name if not location_id and new_location_name else None, # Only if creating new
            new_location_address_1=new_location_address_1 if not location_id and new_location_name else None,
            new_location_city=new_location_city if not location_id and new_location_name else None,
            new_location_postal_code=new_location_postal_code if not location_id and new_location_name else None,
            new_location_latitude=new_location_latitude if not location_id and new_location_name else None,
            new_location_longitude=new_location_longitude if not location_id and new_location_name else None,
            new_location_accessibility=accessibility_list if not location_id and new_location_name else None,
            cost_options=cost_options_data if cost_options_data else None,
            service_areas=service_areas_data if service_areas_data else None,
            service_schedules=schedules_data if schedules_data else None
        )

        updated_offer = data_handler.update_offer(offer_id, offer_update_input)
        if not updated_offer:
            raise HTTPException(status_code=404, detail="Offer not found during update or update failed")

        return RedirectResponse(url=app.url_path_for("offer_detail_view", offer_id=updated_offer.id), status_code=status.HTTP_303_SEE_OTHER)

    except (ValidationError, ValueError) as e:
        error_detail = e.errors() if isinstance(e, ValidationError) else [{"msg": str(e), "loc": ["form"]}]
        # ... (error handling for re-rendering form) ...
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        distinct_service_types = data_handler.get_distinct_service_types()
        # Repopulate form with existing_offer_model + errors
        offer_form_data = existing_offer_model.model_dump()
        # (Need to re-add simplified fields like in edit_offer_form for consistency if re-rendering)
        return templates.TemplateResponse("offer_form.html", {
            "request": request, "offer": offer_form_data, "errors": error_detail,
            "all_organisations": all_organisations, "all_locations": all_locations,
            "distinct_service_types": distinct_service_types,
            "form_action_url": app.url_path_for("edit_offer_action", offer_id=offer_id)
        }, status_code=422)


@app.post("/offers/{offer_id}/delete", name="delete_offer_action")
async def delete_offer_action(offer_id: str):
    deleted = data_handler.delete_offer(offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found for deletion")
    return RedirectResponse(url=app.url_path_for("list_offers_view"), status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server for PostGIS setup.")
    print("Ensure PostgreSQL is running and 'offers_db' is created with PostGIS extension.")
    print("Run 'initialize_database.py' if tables are not set up.")
    print("Run 'migrate_json_to_postgres.py' if data needs to be migrated.")
    # Set ENV VARS for DB connection if not already set in environment:
    # os.environ['PGDATABASE'] = 'offers_db'
    # os.environ['PGUSER'] = 'offer_user'
    # os.environ['PGPASSWORD'] = 'offer_password'
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from pydantic import ValidationError
from typing import List, Optional
import uuid # For new org/loc IDs if not provided via form explicitly

# Assuming models.py and data_handler.py are in the same directory
import models
import data_handler

app = FastAPI(title="Service Offers CRUD App")

# Mount static files directory (for CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

def nl2br(value):
    return Markup(escape(value).replace('\n', '<br>\n'))

templates.env.filters['nl2br'] = nl2br

# --- Dependency for Forms (FastAPI doesn't natively parse Pydantic models from HTML forms directly for complex nested models) ---
# We will handle form parsing manually in each endpoint or use a simpler approach for this example.
# For complex forms, using Pydantic models directly with `request.form()` requires careful handling.

# --- Helper to get base URL for redirects ---
def get_base_url(request: Request) -> str:
    return str(request.base_url)

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse, name="list_offers_view")
async def list_offers_view(
    request: Request,
    service_type: Optional[str] = None,
    city: Optional[str] = None,
    in_person: Optional[bool] = None,
    remote: Optional[bool] = None,
    organisation_name: Optional[str] = None
):
    offers = data_handler.load_offers(
        service_type=service_type,
        city=city,
        in_person=in_person,
        remote=remote,
        organisation_name=organisation_name
    )
    distinct_cities = data_handler.get_distinct_cities()
    distinct_service_types = data_handler.get_distinct_service_types()
    distinct_organisations = data_handler.get_distinct_organisation_names()

    return templates.TemplateResponse(
        "offers_list.html",
        {
            "request": request,
            "offers": offers,
            "distinct_cities": distinct_cities,
            "distinct_service_types": distinct_service_types,
            "distinct_organisations": distinct_organisations,
            "current_filters": { # Pass current filters back to the template to repopulate form
                "service_type": service_type,
                "city": city,
                "in_person": in_person,
                "remote": remote,
                "organisation_name": organisation_name
            }
        },
    )

@app.get("/offers/new", response_class=HTMLResponse, name="create_offer_form")
async def create_offer_form(request: Request):
    all_organisations = data_handler.get_all_organisations()
    all_locations = data_handler.get_all_locations()
    distinct_service_types = data_handler.get_distinct_service_types() # Added for datalist
    return templates.TemplateResponse(
        "offer_form.html",
        {
            "request": request,
            "offer": None, # No existing offer data for a new form
            "all_organisations": all_organisations,
            "all_locations": all_locations,
            "distinct_service_types": distinct_service_types, # Pass to template
            "form_action_url": app.url_path_for("create_offer_action")
        }
    )

@app.post("/offers", name="create_offer_action")
async def create_offer_action(request: Request,
    # Form fields - must match the names in your HTML form
    service_id: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    url: Optional[str] = Form(None), # Pydantic HttpUrl will validate
    status: str = Form("active"),
    type: str = Form(...),
    in_person: bool = Form(False),
    remote: bool = Form(False),
    interpretation_services: bool = Form(False),
    phone_support: bool = Form(False),
    online_support: bool = Form(False),
    # CostOptions - simplified for form handling: assume one cost option for now
    cost_option_amount: float = Form(0.0),
    cost_option_amount_description: Optional[str] = Form("Free for eligible individuals"),
    cost_option_option: str = Form("No Cost"),
    eligibility: Optional[str] = Form(None),
    # ServiceAreas - simplified: assume one service area
    service_area_name: str = Form(...),
    # ServiceSchedules - simplified: assume one schedule
    # For simplicity, not taking all schedule fields, can be expanded
    schedule_description: Optional[str] = Form("Regular weekly operating hours."),
    # Organisation and Location: either select existing or create new
    # For simplicity, this example will focus on selecting existing if IDs are provided.
    # Creating new org/loc via form would require more fields.
    organisation_id: Optional[str] = Form(None), # ID of existing org
    location_id: Optional[str] = Form(None), # ID of existing loc
    # If creating new, these would be needed:
    # new_organisation_name: Optional[str] = Form(None),
    # new_location_name: Optional[str] = Form(None),
    # ... other fields for new org/loc
):
    try:
        cost_options_data = [models.CostOption(amount=cost_option_amount, amount_description=cost_option_amount_description, option=cost_option_option)]
        service_areas_data = [models.ServiceArea(name=service_area_name)]
        # Simplified schedule
        schedules_data = [models.ServiceSchedule(description=schedule_description)]

        # This is a simplified way to handle org/loc. A real form would be more complex.
        # For this example, we primarily rely on selecting existing org/loc by ID.
        # If you wanted to create new org/loc from the same form, you'd need more fields
        # and logic to decide whether to use existing_org_id or new_org_fields.

        # For now, we'll assume that if organisation_id and location_id are provided, they are used.
        # If not, the data_handler.add_offer would need to handle potential inline creation
        # based on offer_data.organisation and offer_data.location being populated.
        # The current OfferCreate model allows for this.

        offer_create_data = models.OfferCreate(
            service_id=service_id, name=name, description=description, url=url or None, status=status, type=type,
            in_person=in_person, remote=remote, interpretation_services=interpretation_services,
            phone_support=phone_support, online_support=online_support,
            cost_options=cost_options_data, eligibility=eligibility, service_areas=service_areas_data,
            service_schedules=schedules_data,
            organisation_id=organisation_id, # Pass the ID
            location_id=location_id, # Pass the ID
            # If new_org_name etc. were provided, you'd populate these instead:
            # organisation=models.OrganisationCreate(name=new_organisation_name, ...) if new_organisation_name else None,
            # location=models.LocationCreate(name=new_location_name, ...) if new_location_name else None,
        )

        new_offer = data_handler.add_offer(offer_create_data)
        # Redirect to the detail page of the newly created offer
        return RedirectResponse(url=app.url_path_for("offer_detail_view", offer_id=new_offer.id), status_code=status.HTTP_303_SEE_OTHER)

    except ValidationError as e:
        # This is a basic error handling. In a real app, you'd show errors on the form.
        print(f"Validation Error: {e.errors()}")
        # For simplicity, redirecting back to form, ideally with error messages.
        # You would need to pass error messages to the template.
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        # Repopulate form with submitted data + errors (complex for full Pydantic models)
        # This is a simplified error display:
        return templates.TemplateResponse("offer_form.html", {
            "request": request, "offer": None, "errors": e.errors(),
            "all_organisations": all_organisations, "all_locations": all_locations,
            "form_action_url": app.url_path_for("create_offer_action")
        }, status_code=422)
    except ValueError as e: # From data_handler for missing org/loc
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        return templates.TemplateResponse("offer_form.html", {
            "request": request, "offer": None, "errors": [{"msg": str(e), "loc": ["form"]}],
             "all_organisations": all_organisations, "all_locations": all_locations,
            "form_action_url": app.url_path_for("create_offer_action")
        }, status_code=400)


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
    distinct_service_types = data_handler.get_distinct_service_types() # Added for datalist

    return templates.TemplateResponse(
        "offer_form.html",
        {
            "request": request,
            "offer": offer.model_dump(), # Pass existing offer data to the form
            "all_organisations": all_organisations,
            "all_locations": all_locations,
            "distinct_service_types": distinct_service_types, # Pass to template
            "form_action_url": app.url_path_for("edit_offer_action", offer_id=offer_id)
        }
    )

@app.post("/offers/{offer_id}/update", name="edit_offer_action")
async def edit_offer_action(request: Request, offer_id: str,
    # Form fields - similar to create, but for update
    service_id: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    status: str = Form(...),
    type: str = Form(...),
    in_person: bool = Form(False),
    remote: bool = Form(False),
    interpretation_services: bool = Form(False),
    phone_support: bool = Form(False),
    online_support: bool = Form(False),
    cost_option_amount: float = Form(...),
    cost_option_amount_description: Optional[str] = Form(None),
    cost_option_option: str = Form(...),
    eligibility: Optional[str] = Form(None),
    service_area_name: str = Form(...),
    schedule_description: Optional[str] = Form(None),
    organisation_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None)
):
    existing_offer = data_handler.get_offer_by_id(offer_id)
    if not existing_offer:
        raise HTTPException(status_code=404, detail="Offer not found to update")

    try:
        cost_options_data = [models.CostOption(amount=cost_option_amount, amount_description=cost_option_amount_description, option=cost_option_option)]
        service_areas_data = [models.ServiceArea(name=service_area_name)]
        schedules_data = [models.ServiceSchedule(description=schedule_description)] # Simplified

        offer_update_data = models.OfferUpdate(
            service_id=service_id, name=name, description=description, url=url or None, status=status, type=type,
            in_person=in_person, remote=remote, interpretation_services=interpretation_services,
            phone_support=phone_support, online_support=online_support,
            cost_options=cost_options_data, eligibility=eligibility, service_areas=service_areas_data,
            service_schedules=schedules_data,
            organisation_id=organisation_id,
            location_id=location_id
        )

        updated_offer = data_handler.update_offer(offer_id, offer_update_data)
        if not updated_offer:
             # Should have been caught by get_offer_by_id earlier, but as a safeguard
            raise HTTPException(status_code=404, detail="Offer not found during update process")

        return RedirectResponse(url=app.url_path_for("offer_detail_view", offer_id=updated_offer.id), status_code=status.HTTP_303_SEE_OTHER)

    except ValidationError as e:
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        return templates.TemplateResponse("offer_form.html", {
            "request": request,
            "offer": existing_offer.model_dump(), # Pass original offer data back
            "errors": e.errors(),
            "all_organisations": all_organisations,
            "all_locations": all_locations,
            "form_action_url": app.url_path_for("edit_offer_action", offer_id=offer_id)
        }, status_code=422)
    except ValueError as e: # From data_handler
        all_organisations = data_handler.get_all_organisations()
        all_locations = data_handler.get_all_locations()
        return templates.TemplateResponse("offer_form.html", {
            "request": request,
            "offer": existing_offer.model_dump(),
            "errors": [{"msg": str(e), "loc": ["form"]}],
            "all_organisations": all_organisations,
            "all_locations": all_locations,
            "form_action_url": app.url_path_for("edit_offer_action", offer_id=offer_id)
        }, status_code=400)


@app.post("/offers/{offer_id}/delete", name="delete_offer_action")
async def delete_offer_action(offer_id: str):
    deleted = data_handler.delete_offer(offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found for deletion")

    # Redirect to the main list view
    # Using status.HTTP_303_SEE_OTHER for POST-redirect-GET pattern
    return RedirectResponse(url=app.url_path_for("list_offers_view"), status_code=status.HTTP_303_SEE_OTHER)


# --- Optional: API endpoints if you want to expose JSON data directly ---
# @app.get("/api/offers", response_model=List[models.Offer])
# async def api_get_offers(
#     service_type: Optional[str] = None,
#     city: Optional[str] = None,
#     in_person: Optional[bool] = None,
#     remote: Optional[bool] = None,
#     organisation_name: Optional[str] = None
# ):
#     return data_handler.load_offers(
#         service_type=service_type, city=city, in_person=in_person, remote=remote, organisation_name=organisation_name
#     )

# @app.get("/api/offers/{offer_id}", response_model=models.Offer)
# async def api_get_offer(offer_id: str):
#     offer = data_handler.get_offer_by_id(offer_id)
#     if not offer:
#         raise HTTPException(status_code=404, detail="Offer not found")
#     return offer

# To run the app (from the terminal, in the project directory):
# uvicorn main:app --reload
# (Ensure main.py contains your FastAPI app instance named 'app')
# (And that offers.json exists or is created, e.g., by running generate_data.py once)

if __name__ == "__main__":
    # This block is for development convenience, not for production deployment.
    # Production servers like Gunicorn or Uvicorn directly target the `app` object.
    # Example: uvicorn main:app --host 0.0.0.0 --port 8000
    import uvicorn
    print("Starting Uvicorn server. Make sure 'offers.json' exists.")
    print("If 'offers.json' does not exist, run 'python generate_data.py > offers.json' first.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Service Offers CRUD Application

This project is a simple CRUD (Create, Read, Update, Delete) service for managing and displaying service offers. It uses FastAPI for the backend API, Jinja2 for HTML templating, and Bootstrap for styling. Service offer locations are displayed using Leaflet.js with an OpenStreetMap basemap. Data is stored in a local `offers.json` file.

## Features

*   **List Offers**: View all available service offers with filtering options.
*   **Create Offers**: Add new service offers through a web form.
*   **View Offer Details**: See comprehensive information for a single offer, including a map of its location.
*   **Edit Offers**: Modify existing service offers.
*   **Delete Offers**: Remove service offers.
*   **Filtering**: Filter offers by service type, city, organisation, in-person availability, and remote availability.
*   **Mapping**: Interactive map display for service offer locations.

## Project Structure

```
.
├── .gitignore
├── generate_data.py    # Script to generate sample offers.json
├── main.py             # FastAPI application logic
├── models.py           # Pydantic models for data validation
├── data_handler.py     # Handles reading/writing to offers.json
├── offers.json         # Data store for service offers (generated)
├── pyproject.toml      # Project metadata and dependencies
├── static/             # Directory for static assets (CSS, JS, images)
└── templates/          # Directory for Jinja2 HTML templates
    ├── base.html
    ├── offer_detail.html
    ├── offer_form.html
    └── offers_list.html
```

## Setup and Installation

Follow these steps to set up and run the project locally:

**1. Clone the Repository (if applicable)**

If you're working with a cloned version of this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

**2. Create a Virtual Environment**

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment (e.g., named .venv)
python -m venv .venv

# Activate the virtual environment
# On Windows:
# .venv\\Scripts\\activate
# On macOS/Linux:
source .venv/bin/activate
```

**3. Install Dependencies**

The project uses `pyproject.toml` to define dependencies. Install them using pip:

```bash
pip install -e .
```
This command installs the dependencies listed in `pyproject.toml` in editable mode.

**4. Generate Sample Data**

The application reads data from `offers.json`. If this file doesn't exist or you want to regenerate it with sample data, run the `generate_data.py` script:

```bash
python generate_data.py > offers.json
```
This will create/overwrite `offers.json` in the root of the project with new sample data.

**5. Run the Application**

Once dependencies are installed and `offers.json` is present, you can run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload
```

*   `main:app` tells Uvicorn to look for an object named `app` in the `main.py` file.
*   `--reload` enables auto-reloading, so the server will restart automatically when you make code changes.

The application will typically be available at `http://127.0.0.1:8000` in your web browser.

## Usage

*   **Home Page (`/`)**: Lists all service offers and provides filtering options.
*   **New Offer (`/offers/new`)**: Displays a form to create a new service offer.
*   **Offer Detail (`/offers/{offer_id}`)**: Shows detailed information about a specific offer, including its location on a map.
*   **Edit Offer (`/offers/{offer_id}/edit`)**: Provides a form to edit an existing offer.
*   **Delete Offer**: Available on the offer list and detail pages.

## Technologies Used

*   **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python.
*   **Uvicorn**: ASGI server for running FastAPI applications.
*   **Pydantic**: Data validation and settings management using Python type annotations.
*   **Jinja2**: Templating engine for Python, used to render HTML pages.
*   **Bootstrap**: Front-end toolkit for designing responsive and mobile-first websites.
*   **Leaflet.js**: Open-source JavaScript library for interactive maps.
*   **OpenStreetMap**: Provides the basemap tiles for Leaflet.
*   **Python**: Programming language used for the backend.
*   **HTML/CSS/JavaScript**: For the frontend presentation and interactivity.

## Potential Future Enhancements

*   User authentication and authorization.
*   More robust form handling for complex list-based fields (e.g., multiple cost options, schedules).
*   Direct creation of new Organisations/Locations from within the offer form.
*   Enhanced error display and feedback on forms.
*   Pagination for the offers list.
*   Automated tests (unit and integration).
*   Deployment to a cloud platform.
*   Using a proper database instead of a JSON file for data storage.
```

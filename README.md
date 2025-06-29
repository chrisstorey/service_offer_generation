# Service Offers CRUD Application

This project is a simple CRUD (Create, Read, Update, Delete) service for managing and displaying service offers. It uses FastAPI for the backend API, Jinja2 for HTML templating, and Bootstrap for styling. Service offer locations are displayed using Leaflet.js with an OpenStreetMap basemap. Data is stored in a **PostgreSQL database with the PostGIS extension** for spatial capabilities.

## Features

*   **List Offers**: View all available service offers with filtering options.
*   **Create Offers**: Add new service offers through a web form.
*   **View Offer Details**: See comprehensive information for a single offer, including a map of its location.
*   **Edit Offers**: Modify existing service offers.
*   **Delete Offers**: Remove service offers.
*   **Filtering**: Filter offers by service type, city, organisation, in-person availability, and remote availability. (Spatial filtering capabilities are now possible with PostGIS, e.g., by distance).
*   **Mapping**: Interactive map display for service offer locations.

## Project Structure

```
.
├── .gitignore
├── initialize_database.py # Script to create PostgreSQL tables
├── migrate_json_to_postgres.py # Script to migrate data from offers.json to PostgreSQL
├── main.py                # FastAPI application logic
├── models.py              # Pydantic models for data validation and DB schema
├── data_handler.py        # Handles database interactions (PostgreSQL/PostGIS)
├── offers.json            # Original data source for migration (not used by running app)
├── pyproject.toml         # Project metadata and dependencies
├── static/                # Directory for static assets (CSS, JS, images) - if used
└── templates/             # Directory for Jinja2 HTML templates
    ├── base.html
    ├── offer_detail.html
    ├── offer_form.html
    └── offers_list.html
```

## Setup and Installation

Follow these steps to set up and run the project locally:

**1. Clone the Repository (if applicable)**

```bash
git clone <repository-url>
cd <repository-directory>
```

**2. Install PostgreSQL and PostGIS**

*   **Install PostgreSQL**: Follow the official instructions for your operating system. (e.g., `sudo apt-get install postgresql postgresql-contrib` on Debian/Ubuntu).
*   **Install PostGIS**: Install the PostGIS extension for your PostgreSQL version (e.g., `sudo apt-get install postgis postgresql-XX-postgis-Y` where XX is PG version and Y is PostGIS version).
*   Ensure the PostgreSQL server is running.

**3. Create Database User and Database**

You'll need a PostgreSQL user and a database for the application.
Default credentials used by the application (can be overridden by environment variables):
    *   Database Name: `offers_db`
    *   User: `offer_user`
    *   Password: `offer_password`

Example commands using `psql` (you might need to run these as the `postgres` superuser, e.g., `sudo -u postgres psql`):
```sql
CREATE USER offer_user WITH PASSWORD 'offer_password';
CREATE DATABASE offers_db OWNER offer_user;
-- Connect to the new database to enable extension:
-- \c offers_db
CREATE EXTENSION IF NOT EXISTS postgis;
```
Ensure the `offer_user` has privileges to connect to `offers_db` and create tables/data.

**4. Set Environment Variables (Optional but Recommended)**

The application uses these environment variables for database connection. If not set, it falls back to the defaults mentioned above.
```bash
export PGDATABASE="offers_db"
export PGUSER="offer_user"
export PGPASSWORD="offer_password"
export PGHOST="localhost"  # Or your PostgreSQL server host
export PGPORT="5432"      # Or your PostgreSQL server port
```

**5. Create a Virtual Environment**

```bash
python -m venv .venv
# On Windows: .venv\\Scripts\\activate
# On macOS/Linux:
source .venv/bin/activate
```

**6. Install Python Dependencies**

Install dependencies using pip (includes `fastapi`, `uvicorn`, `pydantic`, `psycopg2-binary`, `jinja2`):
```bash
pip install -r requirements.txt  # Assuming you create a requirements.txt
# Or, if pyproject.toml is set up for this:
# pip install .
# For now, direct install:
pip install fastapi uvicorn "pydantic>=2.0" psycopg2-binary jinja2 markupsafe python-multipart
```
*(Note: A `requirements.txt` or fully configured `pyproject.toml` is recommended for production).*

**7. Initialize Database Tables**

Run the script to create the necessary tables in your PostgreSQL database:
```bash
python initialize_database.py
```

**8. Migrate Data (Optional)**

If you have an existing `offers.json` file and want to import its data into the PostgreSQL database, run:
```bash
python migrate_json_to_postgres.py
```
*(Note: The `generate_data.py` script can still be used to create a sample `offers.json` if you need one for migration).*

**9. Run the Application**

Use Uvicorn to run the FastAPI application:
```bash
uvicorn main:app --reload
```
The application will typically be available at `http://127.0.0.1:8000`.

## Usage

*   **Home Page (`/`)**: Lists all service offers and provides filtering options.
*   **New Offer (`/offers/new`)**: Displays a form to create a new service offer.
*   **Offer Detail (`/offers/{offer_id}`)**: Shows detailed information about a specific offer, including its location on a map.
*   **Edit Offer (`/offers/{offer_id}/edit`)**: Provides a form to edit an existing offer.
*   **Delete Offer**: Available on the offer list and detail pages.

## Technologies Used

*   **FastAPI**: Web framework for building APIs.
*   **Uvicorn**: ASGI server.
*   **Pydantic**: Data validation and settings management.
*   **PostgreSQL**: Robust open-source relational database.
*   **PostGIS**: Spatial database extender for PostgreSQL. Adds support for geographic objects.
*   **psycopg2-binary**: Python adapter for PostgreSQL.
*   **Jinja2**: Templating engine for HTML.
*   **Bootstrap**: Front-end toolkit (if static files and templates use it).
*   **Leaflet.js**: JavaScript library for interactive maps.
*   **OpenStreetMap**: Basemap tiles for Leaflet.
*   **Python**: Backend programming language.
*   **HTML/CSS/JavaScript**: Frontend.

## Potential Future Enhancements

*   User authentication and authorization.
*   More robust form handling for complex list-based fields (e.g., multiple cost options, schedules).
*   Direct creation of new Organisations/Locations from within the offer form (partially implemented, could be enhanced).
*   Enhanced error display and feedback on forms.
*   Pagination for the offers list.
*   Automated tests (unit and integration).
*   Deployment to a cloud platform.
*   Advanced spatial queries and features using PostGIS (e.g., proximity searches, "offers near me").
```

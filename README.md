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

There are two primary ways to set up and run this project:

1.  **Using Docker Compose (Recommended for ease of use and consistent environment)**
2.  **Manual Local Setup (If you prefer to manage services directly)**

---

### 1. Using Docker Compose

This is the recommended method as it handles the setup of the PostGIS database and the application environment.

**Prerequisites:**
*   Docker: [Install Docker](https://docs.docker.com/get-docker/)
*   Docker Compose: Usually included with Docker Desktop. If not, [install Docker Compose](https://docs.docker.com/compose/install/).

**Steps:**

**a. Clone the Repository (if not already done)**
```bash
git clone <repository-url>
cd <repository-directory>
```

**b. Environment Variables for Docker Compose (Optional - uses defaults)**
The `docker-compose.yml` file is pre-configured with default database credentials:
*   `POSTGRES_USER=offer_user`
*   `POSTGRES_PASSWORD=offer_password`
*   `POSTGRES_DB=offers_db`
The application service (`app`) will automatically use these to connect to the `db` service.
If you need to change these, you can modify them directly in `docker-compose.yml` or set up a `.env` file (see Docker Compose documentation for using `.env` files).

**c. Build and Run the Services**
From the project root directory (where `docker-compose.yml` is located):
```bash
docker-compose up --build
```
*   `--build`: Forces Docker Compose to build the application image from the `Dockerfile` if it's the first time or if changes have been made.
*   This command will start the PostGIS database service and the FastAPI application service.
*   The `entrypoint.sh` script in the `app` service will automatically:
    1.  Wait for the PostgreSQL database to be ready.
    2.  Run `python initialize_database.py` to create the schema and tables (including enabling PostGIS).
    3.  Run `python migrate_json_to_postgres.py` to import data from `offers.json`.
    4.  Start the Uvicorn server for the FastAPI application.

The application will be available at `http://localhost:8000`.

**d. Accessing Services**
*   **Application**: `http://localhost:8000`
*   **PostgreSQL Database**: Can be accessed on `localhost:5432` using the credentials `offer_user`/`offer_password` and database `offers_db` if you need to inspect it directly (e.g., with `psql` or a GUI tool).

**e. Stopping the Services**
Press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the containers (and the network, but not the named volume `postgres_data`):
```bash
docker-compose down
```
To remove containers AND the named volume (deleting all database data):
```bash
docker-compose down -v
```

---

### 2. Manual Local Setup

Follow these steps if you prefer to manage PostgreSQL and the Python environment manually.

**a. Clone the Repository (if applicable)**

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
*(A `requirements.txt` file is provided, so you can also use `pip install -r requirements.txt` after activating the virtual environment).*

**f. Initialize Database Tables**

Run the script to create the necessary tables in your PostgreSQL database:
```bash
python initialize_database.py
```

**g. Migrate Data (Optional)**

If you have an existing `offers.json` file (you can create one using `python generate_data.py > offers.json` if needed) and want to import its data into the PostgreSQL database, run:
```bash
python migrate_json_to_postgres.py
```

**h. Run the Application**

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
*   **PostGIS**: Spatial database extender for PostgreSQL.
*   **psycopg2-binary**: Python adapter for PostgreSQL.
*   **Docker & Docker Compose**: For containerization and service orchestration.
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

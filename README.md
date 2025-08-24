# Safecast API and Dashboard

This project provides a backend API and a frontend dashboard for interacting with the Safecast dataset. It is built with FastAPI and uses a DuckDB database.

## Features

- **User Management**: Sign up, log in, and manage user accounts.
- **Role-Based Access Control**: Assign roles (user, moderator, admin) to users. Admins can manage roles through the UI.
- **API Endpoints**: Secure endpoints for accessing and managing measurements, devices, and bGeigie imports.
- **Interactive Frontend**: A single-page application built with vanilla JavaScript for interacting with the API.

## Project Structure

```
/
├── app/                    # Main application folder
│   ├── routers/            # API endpoint definitions
│   ├── static/             # Frontend CSS and JS
│   ├── templates/          # HTML templates
│   ├── bgeigie_parser.py   # Parser for bGeigie data
│   ├── crud.py             # Database CRUD operations
│   ├── database.py         # Database setup and configuration
│   ├── main.py             # FastAPI application entry point
│   ├── models.py           # SQLAlchemy database models
│   ├── schemas.py          # Pydantic data validation schemas
│   └── security.py         # Authentication and authorization
├── tests/                  # (Not yet implemented)
├── .gitignore
├── install.py              # Installation and admin setup script
├── README.md               # This file
├── requirements.txt        # Python dependencies
└── safecast.db             # DuckDB database file (created on install)
```

## Setup and Installation

### Prerequisites

- Python 3.10+

### 1. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 2. Initialize the Database and Create Admin User

Run the interactive installation script. This will create the `safecast.db` database file and prompt you to create the first admin user.

```bash
python3 install.py
```

Enter an email and a secure password when prompted.

## Running the Application

To start the web server, run the following command from the project root directory:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at [http://localhost:8000](http://localhost:8000). Note that if port 8000 is in use, you may need to run on an alternative port like 8001.

## Usage

1.  **Access the Dashboard**: Open your web browser and navigate to the URL provided when you start the server.
2.  **Sign Up/Login**: Create a new user account or log in with the admin credentials you created during installation.
3.  **Admin Role Management**: If you are logged in as an admin, navigate to the "Users" section to manage user roles. You can assign `admin` or `moderator` privileges to any user via the dropdown menu in the "Actions" column.

# Safecast API and Dashboard

This project provides a complete backend API and frontend dashboard for the Safecast radiation monitoring dataset. It is built with FastAPI and uses a DuckDB database, featuring full bGeigie log file import and processing capabilities with interactive map visualization.

## Features

### Core Functionality
- **User Management**: Sign up, log in, and manage user accounts with JWT authentication
- **Role-Based Access Control**: Assign roles (user, moderator, admin) to users. Admins can manage roles through the UI
- **API Endpoints**: Secure RESTful endpoints for accessing and managing measurements, devices, and bGeigie imports

### bGeigie Import System
- **File Upload**: Upload bGeigie log files (.log format) with automatic validation
- **Data Processing**: Parse multiple bGeigie device formats ($BMRDD, $BGRDD, $BNRDD, etc.) with robust error handling
- **Measurement Extraction**: Extract radiation measurements with CPM to µSv/h conversion (1/334 ratio for LND7317 tube)
- **Interactive Maps**: OpenStreetMap visualization with detailed radiation color scale (12+ levels from black to yellow)
- **Approval Workflow**: Complete workflow from upload → process → metadata submission → admin approval

### Visualization & UI
- **Interactive Frontend**: Single-page application built with vanilla JavaScript and Bootstrap 5
- **Map Features**: Hover tooltips, detailed popups with measurement data, proper marker sizing
- **Data Management**: Filtering, sorting, and status tracking for all imports
- **Responsive Design**: Modern UI with proper error handling and user feedback

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

### Getting Started
1. **Access the Dashboard**: Open your web browser and navigate to [http://localhost:8000](http://localhost:8000)
2. **Sign Up/Login**: Create a new user account or log in with the admin credentials you created during installation
3. **Admin Role Management**: If you are logged in as an admin, navigate to the "Users" section to manage user roles

### bGeigie Import Workflow
1. **Upload Files**: Click "Upload" in the bGeigie Imports section and select a .log file
2. **Process Data**: Click the "Process" button to extract radiation measurements from the uploaded file
3. **View Visualization**: Click on the processed import to view the interactive map with radiation data
4. **Add Metadata**: Fill out the metadata form (cities, description, credits) and click "Submit for Approval"
5. **Admin Approval**: Admins can approve or reject submitted imports using the action buttons

### Map Visualization
- **Color Scale**: Radiation levels displayed with logarithmic color scale from black (very low) to yellow (extreme)
- **Interactive Features**: Hover over measurement points for quick data, click for detailed popups
- **Data Export**: Use "Export Data" button to download measurement data as CSV
- **Toggle Views**: Switch between heatmap and individual measurement point display

### API Access
- **Authentication**: All API endpoints require JWT token authentication
- **Endpoints**: Access `/docs` for interactive API documentation (Swagger UI)
- **Rate Limiting**: API calls are rate-limited for security and performance

## Technical Details

### Supported bGeigie Formats
The parser supports multiple bGeigie device sentence types:
- `$BMRDD` - bGeigie Mini
- `$BGRDD` - bGeigie Classic
- `$BNRDD` - bGeigie Nano
- `$BNXRDD` - bGeigie NX
- `$PNTDD` - Point measurement
- `$CZRDD` - Custom format

### Radiation Conversion
- **CPM to µSv/h**: Uses 1/334 conversion factor for LND7317 Geiger tube
- **Color Scale**: Logarithmic scale with 12+ levels matching original Safecast standards
- **Thresholds**: From <0.03 µSv/h (black) to >100 µSv/h (yellow)

### Database Schema
- **Users**: Authentication and role management
- **BGeigieImports**: File metadata and processing status
- **Measurements**: Individual radiation readings with GPS coordinates
- **Devices**: Device information and relationships

### Security Features
- JWT token-based authentication
- Role-based access control (user/moderator/admin)
- File upload validation and sanitization
- SQL injection protection via SQLAlchemy ORM

## Development

### Adding New Features
1. **Backend**: Add new endpoints in `app/routers/`
2. **Frontend**: Update JavaScript in `app/static/js/`
3. **Database**: Modify models in `app/models.py`
4. **Tests**: Add tests in `tests/` directory (TODO)

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions, please use the GitHub issue tracker or contact the development team.

Can y# NSW Weather Data Visualization Dashboard

A comprehensive web application for visualizing and analyzing weather data from the Australian Bureau of Meteorology (BOM) and other sources.

## Features

- **Interactive Map**: Visualize weather stations across NSW with Leaflet.js
- **Real-time Weather Data**: Fetch current weather conditions using Open-Meteo API
- **Location Search**: Search for locations using OpenStreetMap Nominatim
- **Statistics Dashboard**: View dataset statistics and weather station information
- **RESTful API**: FastAPI backend with comprehensive weather data endpoints

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping
- **GeoAlchemy2**: Spatial database extension for PostGIS
- **PostgreSQL/PostGIS**: Spatial database for weather data
- **Uvicorn**: ASGI web server

### Frontend
- **HTML5/CSS3**: Modern web standards
- **Bootstrap 5**: Responsive CSS framework
- **JavaScript (ES6+)**: Vanilla JavaScript with async/await
- **Leaflet.js**: Interactive maps
- **Chart.js**: Data visualization

### External APIs
- **Open-Meteo**: Current weather data
- **OpenStreetMap Nominatim**: Location search and geocoding

## Project Structure

```
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   ├── api_routes.py        # API endpoints
│   │   └── models.py            # SQLAlchemy models
│   └── database/
│       ├── connection.py        # Database configuration
│       └── models.py            # BOM-specific models
├── frontend/
│   ├── templates/
│   │   └── dashboard.html       # Main dashboard page
│   └── static/
│       ├── css/
│       │   └── dashboard.css    # Dashboard styles
│       └── js/
│           └── dashboard.js     # Dashboard functionality
├── scripts/                     # Utility scripts
├── tests/                       # Test files
├── config/                      # Configuration files
├── docs/                        # Documentation
└── deployment/                  # Deployment configurations
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL with PostGIS extension
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fit3164-ds21
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp config/.env.example config/.env
   # Edit config/.env with your database credentials
   ```

5. **Set up the database**
   ```bash
   # Start PostgreSQL with PostGIS
   docker-compose up -d postgres

   # Initialize database
   python src/database/connection.py
   ```

6. **Run the application**
   ```bash
   # Development server
   python start_server.py

   # Or directly with uvicorn
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Weather Data
- `GET /api/v1/bom/statistics` - Dataset statistics
- `GET /api/v1/bom/stations` - Weather stations
- `GET /api/v1/bom/timeseries` - Time series data
- `GET /api/v1/weather/nearby` - Nearby weather stations

### Current Weather
- `GET /api/v1/weather` - Current weather for coordinates

## Usage

1. **Access the dashboard**: Navigate to `http://localhost:8000/dashboard`
2. **Search locations**: Use the search bar to find locations in Australia
3. **View weather data**: Click on search results to see current weather
4. **Explore stations**: View weather stations on the interactive map
5. **API documentation**: Visit `http://localhost:8000/docs` for API docs

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Type checking
mypy src/

# Linting
flake8 src/

# Formatting
black src/
```

### Database Management
```bash
# Create tables
python init_db.py

# Generate dummy data
python generate_dummy_data.py

# Verify data
python verify_data.py
```

## Configuration

Environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5433/weatherdb

# API Keys (optional)
GOOGLE_MAPS_API_KEY=your_google_maps_key
OWM_API_KEY=your_openweathermap_key

# Application
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
```

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Publish Docker image to GitHub Container Registry (GHCR)

This repository includes a GitHub Actions workflow that builds and publishes the Docker image to GitHub Container Registry on push to the `main` branch.

1. Enable GitHub Packages/Container registry for your account or organization
   - Go to `Settings -> Packages` and enable GitHub Packages if necessary.

2. After pushing to `main`, the workflow will publish the image as:
   - `ghcr.io/<your-github-username>/fit3164-dashboard:latest`
   - `ghcr.io/<your-github-username>/fit3164-dashboard:<commit-sha>`

3. To pull and run the image on macOS:

```bash
# Log in to GHCR (use a personal access token with `read:packages` scope)
echo $CR_PAT | docker login ghcr.io -u <github-username> --password-stdin

# Pull the published image
docker pull ghcr.io/<github-username>/fit3164-dashboard:latest

# Run the container (ensure Postgres/Redis are accessible)
docker run -d -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:password@<postgres-host>:5432/weatherdb" \
  ghcr.io/<github-username>/fit3164-dashboard:latest
```

Note: replace `<github-username>` and `<postgres-host>` as appropriate.

### Production Deployment
```bash
# Using gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Australian Bureau of Meteorology (BOM) for weather data
- Open-Meteo for current weather API
- OpenStreetMap for geocoding services

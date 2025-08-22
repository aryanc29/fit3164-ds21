# Weather Data Visualization Backend

A FastAPI-based backend service for the Interactive Visualisation of Spatial Weather Data platform. This backend provides APIs for weather data ingestion, processing, and visualization support.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git (for cloning the repository)

### Getting Started

1. **Clone and navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   # Edit .env and add your actual API keys (NEVER commit this file)
   ```

3. **Start the development environment**
   
   **Windows:**
   ```bash
   start-dev.bat
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

3. **Access the services**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Database Admin: http://localhost:5050 (optional)

## 🏗️ Architecture

### Technology Stack
- **FastAPI**: Modern Python web framework
- **PostgreSQL + PostGIS**: Geospatial database
- **Redis**: Caching and session storage
- **Docker**: Containerization
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations

### Key Features
- ✅ RESTful API for weather data
- ✅ Real-time data ingestion from BOM and Meteostat APIs
- ✅ CSV/Excel file upload and processing
- ✅ Geospatial data support with PostGIS
- ✅ Redis caching for performance
- ✅ JWT authentication with 2FA support
- ✅ Data export capabilities
- ✅ Comprehensive data validation

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/            # API routes and endpoints
│   ├── core/           # Core configuration and utilities
│   ├── models/         # Database models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic services
│   └── utils/          # Utility functions
├── docker-compose.yml  # Docker services configuration
├── Dockerfile         # Backend container definition
├── requirements.txt   # Python dependencies
└── main.py           # Application entry point
```

## 🔧 Configuration

⚠️ **Security Note**: Never commit API keys or secrets to the repository!

The application uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

**Important**: The `.env` file is in `.gitignore` and should never be committed. Update it with your actual API keys:

Key configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret key
- `JWT_SECRET_KEY`: JWT signing key
- `BOM_API_BASE_URL`: Bureau of Meteorology API endpoint
- `METEOSTAT_API_KEY`: Meteostat API key (optional)

## 🌐 API Endpoints

### Weather Data
- `GET /api/v1/weather/stations` - List weather stations
- `GET /api/v1/weather/stations/{station_id}` - Get specific station
- `GET /api/v1/weather/observations` - Get weather observations
- `GET /api/v1/weather/observations/latest` - Get latest observations
- `GET /api/v1/weather/geojson` - Get stations as GeoJSON

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### File Upload
- `POST /api/v1/upload/csv` - Upload CSV weather data
- `GET /api/v1/upload/status/{upload_id}` - Check upload status

### Data Export
- `GET /api/v1/export/csv` - Export weather data as CSV
- `GET /api/v1/export/geojson` - Export weather data as GeoJSON

## 🗄️ Database Schema

### Core Tables
- **weather_stations**: Weather station metadata and locations
- **weather_observations**: Weather observation data
- **users**: User accounts and authentication
- **user_datasets**: User-uploaded datasets
- **user_observations**: User-uploaded weather data

### Features
- PostGIS integration for geospatial queries
- Automatic timestamp management
- UUID primary keys for security
- Comprehensive indexing for performance

## 🔐 Security Features

- JWT-based authentication
- Two-factor authentication (2FA) support
- Password hashing with bcrypt
- Rate limiting
- CORS protection
- Input validation and sanitization
- SQL injection prevention

## 📊 Data Sources

### Bureau of Meteorology (BOM)
- Real-time weather observations
- Historical weather data
- Weather station metadata

### Meteostat API
- Global weather data
- Historical climate data
- Station information

### User Uploads
- CSV file processing
- Excel file support
- Data validation and cleaning

## 🚀 Development

### Running Locally
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U weather_user -d weather_db

# Run migrations (when implemented)
docker-compose exec backend alembic upgrade head
```

### Testing
```bash
# Run tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app
```

## 📈 Performance

### Caching Strategy
- Redis caching for frequently accessed data
- Cache TTL based on data volatility
- Cache invalidation on data updates

### Database Optimization
- Proper indexing on frequently queried fields
- Connection pooling
- Query optimization for large datasets

### Rate Limiting
- API rate limiting to prevent abuse
- Per-user rate limits
- Configurable limits per endpoint

## 🔍 Monitoring

### Health Checks
- Application health endpoint
- Database connectivity checks
- Redis connectivity checks
- External API availability

### Logging
- Structured logging with JSON format
- Request/response logging
- Error tracking and reporting
- Performance metrics

## 🚢 Deployment

### Production Considerations
- Update security keys and passwords
- Configure proper CORS origins
- Set up SSL/HTTPS
- Configure log aggregation
- Set up monitoring and alerting
- Database backup strategy

### Environment Variables for Production
```bash
DEBUG=false
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@prod-db:5432/weather_db
REDIS_URL=redis://prod-redis:6379/0
ALLOWED_HOSTS=["yourdomain.com"]
```

## 🤝 Contributing

1. Create feature branch
2. Follow code style guidelines
3. Add tests for new features
4. Update documentation
5. Submit pull request

## 📝 API Documentation

Full API documentation is available at `/docs` when running the application. This includes:
- Interactive API explorer
- Request/response schemas
- Authentication examples
- Error code descriptions

## ⚡ Performance Targets

Based on project requirements:
- **Response Time**: <2 seconds for datasets with <1000 records
- **Availability**: 99.9% uptime
- **Throughput**: Support concurrent users
- **Data Processing**: Real-time ingestion capability

## 🔗 Related Services

This backend is designed to work with:
- React frontend application
- External weather APIs (BOM, Meteostat)
- PostgreSQL database
- Redis cache
- File storage services

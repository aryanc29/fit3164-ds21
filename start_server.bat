@echo off
echo 🚀 Starting Weather Data Visualization System
echo.

echo 📋 Loading configuration from .env file...
echo 🔍 Checking database connection...
docker-compose ps postgres

echo 🌐 Starting web server...
echo Frontend will be available at: http://localhost:8000/
echo API docs will be available at: http://localhost:8000/docs
echo.

python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

@echo off
REM Weather Data Visualization Backend - Development Startup Script (Windows)

echo 🌤️  Weather Data Visualization Backend
echo ======================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Copy environment file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from .env.example
    copy .env.example .env
    echo ⚠️  Please review and update the .env file with your configuration
)

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

echo 🔍 Checking service health...

REM Check if services are responding
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get -TimeoutSec 5 | Out-Null; echo '✅ Backend API is ready' } catch { echo '❌ Backend API is not ready yet' }"

echo.
echo 🚀 Services are starting up!
echo.
echo 📡 API Documentation: http://localhost:8000/docs
echo 🗄️  Database Admin (pgAdmin): http://localhost:5050 (start with: docker-compose --profile admin up -d)
echo 📊 API Health Check: http://localhost:8000/health
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down
echo To rebuild: docker-compose up --build

pause

#!/usr/bin/env python3
"""
Start the Weather Data Visualization Server
Loads configuration from .env file automatically
"""
import os
import subprocess
import sys
from dotenv import load_dotenv

def main():
    """Start the weather visualization server"""
    print("🚀 Starting Weather Data Visualization System")
    print("=" * 50)
    
    # Load environment variables from .env file
    print("📋 Loading configuration from .env file...")
    load_dotenv()
    
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = os.getenv("API_PORT", "8000")
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ Error: DATABASE_URL not found in .env file")
        sys.exit(1)
    
    print(f"✅ Database URL configured: {database_url.split('@')[0]}@...")
    print(f"🌐 Server will run on: http://{host}:{port}/")
    print(f"📖 API docs will be at: http://{host}:{port}/docs")
    print()
    
    # Check if Docker containers are running
    try:
        result = subprocess.run(["docker-compose", "ps", "postgres"], 
                              capture_output=True, text=True, cwd=".")
        if "Up" not in result.stdout:
            print("⚠️ Warning: PostgreSQL container may not be running")
            print("💡 Try running: docker-compose up -d")
            print()
    except FileNotFoundError:
        print("⚠️ Warning: Docker Compose not found")
        print()
    
    # Start the server
    print("🎯 Starting FastAPI server...")
    try:
        subprocess.run([
            "python", "-m", "uvicorn", "main:app",
            "--host", host,
            "--port", port,
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()

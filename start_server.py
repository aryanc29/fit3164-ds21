#!/usr/bin/env python3
"""
Start the Weather Data Visualization Server
Loads configuration from .env file automatically
"""
import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path

def main():
    """Start the weather visualization server"""
    print("🚀 Starting Weather Data Visualization System")
    print("=" * 50)
    
    # Get the project root directory (where this script is located)
    project_root = Path(__file__).parent.absolute()
    env_file = project_root / "config" / ".env"
    
    # Load environment variables from .env file
    print(f"📋 Loading configuration from: {env_file}")
    print(f"📂 Project root: {project_root}")
    print(f"📄 .env file exists: {env_file.exists()}")
    
    if not env_file.exists():
        print(f"❌ Error: .env file not found at {env_file}")
        print("💡 Make sure .env file exists in the config directory")
        print("💡 Current directory contents:")
        try:
            for item in project_root.iterdir():
                print(f"   - {item.name}")
            if (project_root / "config").exists():
                print("💡 Config directory contents:")
                for item in (project_root / "config").iterdir():
                    print(f"   - config/{item.name}")
        except Exception as e:
            print(f"   Error listing directory: {e}")
        sys.exit(1)
    
    # Try to load the .env file
    print("🔄 Attempting to load .env file...")
    result = load_dotenv(env_file)
    print(f"📋 dotenv load result: {result}")
    
    # Debug: Show all environment variables containing 'DATABASE'
    print("🔍 Environment variables with 'DATABASE':")
    for key, value in os.environ.items():
        if 'DATABASE' in key.upper():
            print(f"   {key} = {value}")
    
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = os.getenv("API_PORT", "8000")
    database_url = os.getenv("DATABASE_URL")
    
    print(f"🌐 API_HOST: {host}")
    print(f"🌐 API_PORT: {port}")
    print(f"🗄️ DATABASE_URL: {database_url}")
    
    if not database_url:
        print("❌ Error: DATABASE_URL not found in .env file")
        print("💡 Check that your .env file contains:")
        print("   DATABASE_URL=postgresql://username:password@localhost:5432/weather_db")
        print()
        print("🔍 Let's check the .env file content:")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                print("📄 .env file content:")
                for line_num, line in enumerate(content.split('\n'), 1):
                    if line.strip() and not line.strip().startswith('#'):
                        print(f"   Line {line_num}: {line}")
        except Exception as e:
            print(f"   Error reading .env file: {e}")
        sys.exit(1)
    
    print(f"✅ Database URL configured: {database_url.split('@')[0]}@...")
    print(f"🌐 Server will run on: http://{host}:{port}/")
    print(f"📖 API docs will be at: http://{host}:{port}/docs")
    print()
    
    # Check if Docker containers are running
    try:
        result = subprocess.run(["docker-compose", "ps", "postgres"], 
                              capture_output=True, text=True, cwd=project_root)
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
            "python", "-m", "uvicorn", "src.api.main:app",
            "--host", host,
            "--port", port,
            "--reload"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
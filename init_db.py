#!/usr/bin/env python3
"""
Database initialization script
Sets up PostGIS extension and creates initial schema
"""

import pg8000
import os
from app.database.connection import engine, Base

def setup_postgis():
    """Set up PostGIS extension in the database"""
    try:
        # Connection parameters
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/weatherdb")
        
        # Parse connection string
        if db_url.startswith("postgresql://"):
            # Remove postgresql:// prefix
            connection_part = db_url[13:]
            user_pass, host_db = connection_part.split("@")
            user, password = user_pass.split(":")
            host_port, database = host_db.split("/")
            host, port = host_port.split(":")
            
            # Connect to database
            conn = pg8000.connect(
                host=host,
                port=int(port),
                database=database,
                user=user,
                password=password
            )
            
            # Enable autocommit for extension creation
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create PostGIS extension
            print("🗺️  Setting up PostGIS extension...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
            
            # Verify PostGIS installation
            cursor.execute("SELECT PostGIS_Version();")
            version = cursor.fetchone()
            if version:
                print(f"✅ PostGIS version: {version[0]}")
            
            # Close connections
            cursor.close()
            conn.close()
            
            print("✅ PostGIS setup completed successfully!")
            
    except Exception as e:
        print(f"❌ PostGIS setup failed: {e}")
        raise

def create_tables():
    """Create all database tables"""
    try:
        print("📋 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        raise

def main():
    """Main initialization function"""
    print("🚀 Initializing Weather Database with PostGIS...")
    
    # Step 1: Set up PostGIS extension
    setup_postgis()
    
    # Step 2: Create tables
    create_tables()
    
    print("🎉 Database initialization completed!")

if __name__ == "__main__":
    main()

"""
Fast ingest of matches.csv into bom_weather_stations table using COPY.

Usage:
  python ingest_matches.py --csv d:/FIT3164/data/matches.csv --db "postgresql://user:pass@host:port/dbname"

Or set DATABASE_URL environment variable and run:
  python ingest_matches.py --csv d:/FIT3164/data/matches.csv
"""
import argparse
import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from io import StringIO


def get_db_url(args_db_url):
    """Get database URL from args or environment."""
    if args_db_url:
        return args_db_url
    # Try environment variables
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url
    # Try to construct from individual env vars
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    user = os.environ.get('DB_USER', 'postgres')
    password = os.environ.get('DB_PASSWORD', 'password')
    dbname = os.environ.get('DB_NAME', 'weatherdb')
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def prepare_data(csv_path):
    """Read matches.csv and prepare for database insertion."""
    df = pd.read_csv(csv_path)
    
    # Clean and prepare columns for database
    df_clean = df.copy()
    
    # Use bom_name as station_name, handle duplicates
    df_clean = df_clean.drop_duplicates(subset=['bom_name', 'site'], keep='first')
    
    # Select and rename columns to match database schema (only name, lat, lon)
    df_out = df_clean[['bom_name', 'lat', 'lon']].rename(columns={
        'bom_name': 'station_name',
        'lat': 'latitude',
        'lon': 'longitude'
    })
    
    return df_out


def ingest_to_postgres(df, db_url, table_name='bom_weather_stations'):
    """Use COPY to bulk insert data into PostgreSQL."""
    print(f"Connecting to database...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        # Create table if it doesn't exist
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            station_name VARCHAR(255) NOT NULL,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            location GEOGRAPHY(POINT, 4326),
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(station_name)
        );
        """
        cur.execute(create_table_sql)
        print(f"Table {table_name} ready")
        
        # Prepare CSV data in memory
        output = StringIO()
        df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N')
        output.seek(0)
        
        # Use COPY for fast bulk insert with ON CONFLICT handling
        copy_sql = f"""
        COPY {table_name} (station_name, latitude, longitude) 
        FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')
        """
        
        cur.copy_expert(copy_sql, output)
        
        # Update location column using PostGIS
        print("Updating PostGIS location column...")
        update_location_sql = f"""
        UPDATE {table_name} 
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """
        cur.execute(update_location_sql)
        
        # Get count of inserted rows
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        
        conn.commit()
        print(f"Successfully ingested {len(df)} rows into {table_name}")
        print(f"Total rows in table: {count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during ingestion: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Ingest matches.csv into PostgreSQL')
    parser.add_argument('--csv', default=r'd:\FIT3164\data\matches.csv', help='Path to matches.csv')
    parser.add_argument('--db', help='Database URL (postgresql://user:pass@host:port/dbname)')
    parser.add_argument('--table', default='bom_weather_stations', help='Target table name')
    
    args = parser.parse_args()
    
    # Get database URL
    db_url = get_db_url(args.db)
    print(f"Using database: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
    
    # Prepare data
    print(f"Reading {args.csv}...")
    df = prepare_data(args.csv)
    print(f"Prepared {len(df)} unique records for ingestion")
    
    # Ingest to database
    ingest_to_postgres(df, db_url, args.table)
    print("Ingestion complete!")


if __name__ == '__main__':
    main()
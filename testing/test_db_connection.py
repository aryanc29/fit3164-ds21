#!/usr/bin/env python3
"""
Database connection test script to find correct credentials
"""

import psycopg2
import getpass

def test_connection(host, port, user, password, database):
    """Test a single database connection"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"Failed: {e}")
        return False

def main():
    """Test common PostgreSQL configurations"""
    
    print("Testing PostgreSQL database connections...")
    
    # Common configurations to test
    configs = [
        ("localhost", 5432, "postgres", "", "postgres"),  # No password
        ("localhost", 5432, "postgres", "postgres", "postgres"),  # Password = postgres
        ("localhost", 5432, "postgres", "admin", "postgres"),  # Password = admin
        ("localhost", 5432, "postgres", "password", "postgres"),  # Password = password
    ]
    
    for host, port, user, password, database in configs:
        print(f"\nTrying: {user}@{host}:{port}/{database} (password: {'empty' if not password else password})")
        if test_connection(host, port, user, password, database):
            print(f"✅ SUCCESS! Connection string: postgresql://{user}:{password}@{host}:{port}/{database}")
            
            # Test if weatherdb exists
            print("Testing if 'weatherdb' database exists...")
            if test_connection(host, port, user, password, "weatherdb"):
                print(f"✅ weatherdb exists! Use: postgresql://{user}:{password}@{host}:{port}/weatherdb")
            else:
                print("❌ weatherdb does not exist. You can create it or use 'postgres' database.")
            
            return True
    
    # If none worked, prompt user
    print("\n❌ None of the common configurations worked.")
    print("Please provide your PostgreSQL credentials:")
    
    user = input("Username (default: postgres): ").strip() or "postgres"
    password = getpass.getpass("Password: ")
    host = input("Host (default: localhost): ").strip() or "localhost"
    port = input("Port (default: 5432): ").strip() or "5432"
    database = input("Database (default: postgres): ").strip() or "postgres"
    
    print(f"\nTesting custom configuration...")
    if test_connection(host, int(port), user, password, database):
        print(f"✅ SUCCESS! Connection string: postgresql://{user}:{password}@{host}:{port}/{database}")
        return True
    else:
        print("❌ Custom configuration also failed.")
        return False

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Database schema fix script for Safecast API
Adds missing device_id column to measurements table
"""

import duckdb
import os

def fix_database_schema():
    db_path = "safecast.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        # Connect to DuckDB
        conn = duckdb.connect(db_path)
        
        # Check if device_id column exists in measurements table
        result = conn.execute("DESCRIBE measurements").fetchall()
        columns = [row[0] for row in result]
        
        print("Current measurements table columns:", columns)
        
        if 'device_id' not in columns:
            print("Adding device_id column to measurements table...")
            conn.execute("ALTER TABLE measurements ADD COLUMN device_id INTEGER")
            print("✓ device_id column added successfully")
        else:
            print("✓ device_id column already exists")
        
        # Verify the change
        result = conn.execute("DESCRIBE measurements").fetchall()
        print("Updated measurements table structure:")
        for row in result:
            print(f"  {row[0]} - {row[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    print("Fixing Safecast API database schema...")
    success = fix_database_schema()
    if success:
        print("Database schema fixed successfully!")
    else:
        print("Failed to fix database schema.")

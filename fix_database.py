"""
Fix Database Script
This script will recreate the database with all required tables.
WARNING: This will delete all existing data!
"""

import os
import sqlite3

DB_PATH = 'instance/users.db'

def fix_database():
    print("=" * 60)
    print("Database Fix Script")
    print("=" * 60)
    
    if os.path.exists(DB_PATH):
        response = input(f"\nDatabase file exists at {DB_PATH}\nDelete and recreate? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        try:
            os.remove(DB_PATH)
            print(f"✓ Deleted existing database: {DB_PATH}")
        except Exception as e:
            print(f"Error deleting database: {e}")
            return
    else:
        print(f"Database file doesn't exist. Will be created at: {DB_PATH}")
    
    print("\n✓ Database will be recreated when you run the Flask app.")
    print("  Run: python app.py")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    fix_database()


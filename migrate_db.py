"""
Database Migration Script
Run this script to update your existing database with the new 'verified' column.
This script will:
1. Add the 'verified' column to the User table
2. Mark all existing users as verified (for backward compatibility)
3. Create the OTP table if it doesn't exist
"""

import sqlite3
import os

DB_PATH = 'instance/users.db'

def migrate_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("The database will be created automatically when you run the app.")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if 'verified' column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' not in columns:
            print("Adding 'verified' column to User table...")
            cursor.execute("ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 1")
            cursor.execute("UPDATE user SET verified = 1 WHERE verified IS NULL")
            conn.commit()
            print("✓ 'verified' column added successfully!")
            print("✓ All existing users have been marked as verified.")
        else:
            print("✓ 'verified' column already exists.")
        
        # Check if OTP table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='otp'")
        if not cursor.fetchone():
            print("Creating OTP table...")
            cursor.execute("""
                CREATE TABLE otp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(150) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    created_at DATETIME,
                    expires_at DATETIME NOT NULL,
                    verified BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            conn.commit()
            print("✓ OTP table created successfully!")
        else:
            print("✓ OTP table already exists.")
        
        conn.close()
        print("\n✓ Database migration completed successfully!")
        print("You can now run your Flask app.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        print("\nAlternative: Delete the database file and let the app recreate it:")
        print(f"  Delete: {DB_PATH}")

if __name__ == '__main__':
    migrate_database()


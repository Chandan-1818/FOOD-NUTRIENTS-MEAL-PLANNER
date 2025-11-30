"""
Script to delete all user data from the database.
This will delete:
- All users
- All health data
- All password reset tokens
- All email verification OTPs
"""

from app import app, db, User, HealthData, PasswordReset, EmailVerification
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def delete_all_user_data():
    """Delete all user data from all tables"""
    with app.app_context():
        try:
            print("="*60)
            print("DELETING ALL USER DATA")
            print("="*60)
            
            # Count records before deletion
            user_count = User.query.count()
            health_data_count = HealthData.query.count()
            password_reset_count = PasswordReset.query.count()
            email_verification_count = EmailVerification.query.count()
            
            print(f"\nCurrent data:")
            print(f"  Users: {user_count}")
            print(f"  Health Data Records: {health_data_count}")
            print(f"  Password Reset Tokens: {password_reset_count}")
            print(f"  Email Verification OTPs: {email_verification_count}")
            
            if user_count == 0 and health_data_count == 0:
                print("\n✓ Database is already empty. Nothing to delete.")
                return
            
            # Delete in order (respecting foreign key constraints)
            print("\nDeleting data...")
            
            # Delete health data first (has foreign key to user)
            deleted_health = HealthData.query.delete()
            print(f"  ✓ Deleted {deleted_health} health data records")
            
            # Delete password reset tokens
            deleted_reset = PasswordReset.query.delete()
            print(f"  ✓ Deleted {deleted_reset} password reset tokens")
            
            # Delete email verification OTPs
            deleted_otp = EmailVerification.query.delete()
            print(f"  ✓ Deleted {deleted_otp} email verification OTPs")
            
            # Delete users last
            deleted_users = User.query.delete()
            print(f"  ✓ Deleted {deleted_users} users")
            
            # Commit the changes
            db.session.commit()
            
            print("\n" + "="*60)
            print("✓ ALL USER DATA DELETED SUCCESSFULLY")
            print("="*60)
            
            # Verify deletion
            remaining_users = User.query.count()
            remaining_health = HealthData.query.count()
            
            if remaining_users == 0 and remaining_health == 0:
                print("\n✓ Verification: Database is now empty.")
            else:
                print(f"\n⚠️  Warning: Some data may remain (Users: {remaining_users}, Health Data: {remaining_health})")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error deleting user data: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    import sys
    
    # Check if --force flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Auto-confirm deletion
        delete_all_user_data()
    else:
        # Confirm before deletion
        print("\n⚠️  WARNING: This will delete ALL user data!")
        print("   - All users")
        print("   - All health data")
        print("   - All password reset tokens")
        print("   - All email verification OTPs")
        print("\nThis action cannot be undone!")
        print("\nTo skip confirmation, run: python delete_all_users.py --force")
        
        response = input("\nType 'DELETE ALL' to confirm: ")
        
        if response == 'DELETE ALL':
            delete_all_user_data()
        else:
            print("\n❌ Deletion cancelled. No data was deleted.")


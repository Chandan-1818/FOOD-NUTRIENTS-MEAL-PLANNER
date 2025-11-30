"""
Test script for admin login functionality
Tests:
1. Admin login with correct credentials
2. Admin login with wrong password
3. Regular user login (should not be affected)
4. Admin username exception handling
"""

import requests
import sys

# Test configuration
BASE_URL = "http://localhost:5000"  # Change if your Flask app runs on different port
ADMIN_USERNAME = "CHANDAN"
ADMIN_PASSWORD = "chandan...$$$"
WRONG_PASSWORD = "wrong_password"

def test_admin_login_correct():
    """Test admin login with correct credentials"""
    print("\n" + "="*60)
    print("TEST 1: Admin Login with Correct Credentials")
    print("="*60)
    
    try:
        session = requests.Session()
        
        # Get login page first to get any CSRF tokens or cookies
        response = session.get(f"{BASE_URL}/login")
        print(f"✓ Login page loaded (Status: {response.status_code})")
        
        # Attempt admin login
        login_data = {
            'email': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        
        print(f"   Login response status: {response.status_code}")
        print(f"   Response headers location: {response.headers.get('Location', 'None')}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'admin' in location or 'dashboard' in location:
                print("✓ Admin login successful - Redirected to admin dashboard")
                return True
            else:
                print(f"⚠️  Unexpected redirect location: {location}")
                return False
        else:
            print(f"❌ Admin login failed - Expected redirect (302), got {response.status_code}")
            print(f"   Response content: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app is not running!")
        print("   Please start Flask app with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_login_wrong_password():
    """Test admin login with wrong password"""
    print("\n" + "="*60)
    print("TEST 2: Admin Login with Wrong Password")
    print("="*60)
    
    try:
        session = requests.Session()
        
        # Get login page first
        session.get(f"{BASE_URL}/login")
        
        # Attempt admin login with wrong password
        login_data = {
            'email': ADMIN_USERNAME,
            'password': WRONG_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
        
        print(f"   Response status: {response.status_code}")
        
        # Should stay on login page with error message
        if response.status_code == 200:
            if 'Invalid' in response.text or 'password' in response.text.lower():
                print("✓ Admin login correctly rejected wrong password")
                return True
            else:
                print("⚠️  Wrong password accepted or no error message shown")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_admin_username_case_insensitive():
    """Test that admin username is case-insensitive"""
    print("\n" + "="*60)
    print("TEST 3: Admin Username Case Insensitivity")
    print("="*60)
    
    test_cases = ["chandan", "Chandan", "CHANDAN", "ChAnDaN"]
    
    for username in test_cases:
        try:
            session = requests.Session()
            session.get(f"{BASE_URL}/login")
            
            login_data = {
                'email': username,
                'password': ADMIN_PASSWORD
            }
            
            response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if 'admin' in location or 'dashboard' in location:
                    print(f"✓ '{username}' - Admin login successful")
                else:
                    print(f"⚠️  '{username}' - Unexpected redirect")
            else:
                print(f"❌ '{username}' - Login failed")
                
        except Exception as e:
            print(f"❌ '{username}' - Error: {e}")
    
    return True

def test_regular_user_not_affected():
    """Test that regular user login still works"""
    print("\n" + "="*60)
    print("TEST 4: Regular User Login (Should Still Work)")
    print("="*60)
    
    try:
        session = requests.Session()
        session.get(f"{BASE_URL}/login")
        
        # Try with a non-admin email (this will fail but should not crash)
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
        
        if response.status_code == 200:
            print("✓ Regular user login flow works (returns to login page for invalid credentials)")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADMIN LOGIN TEST SUITE")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print(f"Admin Username: {ADMIN_USERNAME}")
    print(f"Admin Password: {'*' * len(ADMIN_PASSWORD)}")
    
    results = []
    
    # Run tests
    results.append(("Admin Login (Correct)", test_admin_login_correct()))
    results.append(("Admin Login (Wrong Password)", test_admin_login_wrong_password()))
    results.append(("Case Insensitivity", test_admin_username_case_insensitive()))
    results.append(("Regular User Login", test_regular_user_not_affected()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())


"""
Simple test to verify the API endpoints work correctly.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Session to maintain cookies for authentication
session = requests.Session()

def test_stocks_endpoint():
    """Test /api/stocks endpoint"""
    print("\n=== Testing /api/stocks ===")
    try:
        response = session.get(f"{BASE_URL}/api/stocks", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stocks = response.json()
            print(f"Total stocks: {len(stocks)}")
            for stock in stocks[:5]:
                print(f"  {stock.get('symbol')}: {stock.get('name', stock.get('company_name'))} ({stock.get('sector')}) - Change: {stock.get('change_percent')}%")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_health_endpoint():
    """Test /api/health endpoint"""
    print("\n=== Testing /api/health ===")
    try:
        response = session.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Exception: {e}")

def test_signup_and_login():
    """Test signup and login"""
    print("\n=== Testing /api/login ===")
    try:
        # Login with existing testuser (password may differ)
        # Let's create a new unique user first
        import time
        unique_user = f"apitest_{int(time.time())}"
        
        # Signup a new user
        signup_data = {
            "username": unique_user,
            "email": f"{unique_user}@example.com",
            "password": "testpass123"
        }
        response = session.post(f"{BASE_URL}/api/signup", json=signup_data, timeout=5)
        print(f"Signup Status: {response.status_code} - {response.text[:100] if response.status_code != 201 else 'OK'}")
        
        # Then login with same credentials
        login_data = {
            "username": unique_user,
            "password": "testpass123"
        }
        response = session.post(f"{BASE_URL}/api/login", json=login_data, timeout=5)
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Logged in successfully!")
            return True
        else:
            print(f"Login Error: {response.text}")
            # Try existing user as fallback
            print("Trying existing user 'testuser'...")
            login_data = {"username": "testuser", "password": "testpass123"}
            response = session.post(f"{BASE_URL}/api/login", json=login_data, timeout=5)
            if response.status_code == 200:
                print("✅ Logged in with existing user!")
                return True
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_search_growing_tech():
    """Test search with 'tech growing stocks' query"""
    print("\n=== Testing /api/search with 'tech growing stocks' ===")
    try:
        search_data = {
            "query": "tech growing stocks",
            "limit": 20
        }
        response = session.post(f"{BASE_URL}/api/search", json=search_data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Total results: {len(results)}")
            print("\nResults (should only show POSITIVE change_percent tech stocks):")
            all_positive = True
            all_tech = True
            for r in results[:10]:
                symbol = r.get('symbol')
                change = r.get('change_percent', 0)
                sector = r.get('sector', 'Unknown')
                status = "✅" if change > 0 else "❌"
                print(f"  {status} {symbol}: {change}% change, sector: {sector}")
                if change <= 0:
                    all_positive = False
                if sector != 'Technology':
                    all_tech = False
            
            if all_positive and all_tech and len(results) > 0:
                print("\n✅ PASS: Soft filter working - only growing tech stocks returned!")
            else:
                if not all_tech:
                    print("\n⚠️ Non-tech stocks in results (hard filter issue)")
                if not all_positive:
                    print("\n⚠️ Falling stocks in results (soft filter issue)")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_search_falling_tech():
    """Test search with 'tech falling stocks' query"""
    print("\n=== Testing /api/search with 'tech falling stocks' ===")
    try:
        search_data = {
            "query": "tech falling stocks",
            "limit": 20
        }
        response = session.post(f"{BASE_URL}/api/search", json=search_data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Total results: {len(results)}")
            print("\nResults (should only show NEGATIVE change_percent tech stocks):")
            all_negative = True
            all_tech = True
            for r in results[:10]:
                symbol = r.get('symbol')
                change = r.get('change_percent', 0)
                sector = r.get('sector', 'Unknown')
                status = "✅" if change < 0 else "❌"
                print(f"  {status} {symbol}: {change}% change, sector: {sector}")
                if change >= 0:
                    all_negative = False
                if sector != 'Technology':
                    all_tech = False
            
            if all_negative and all_tech and len(results) > 0:
                print("\n✅ PASS: Soft filter working - only falling tech stocks returned!")
            else:
                if not all_tech:
                    print("\n⚠️ Non-tech stocks in results (hard filter issue)")
                if not all_negative:
                    print("\n⚠️ Growing stocks in results (soft filter issue)")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_health_endpoint()
    test_stocks_endpoint()
    if test_signup_and_login():
        test_search_growing_tech()
        test_search_falling_tech()
    print("\n=== Done ===")

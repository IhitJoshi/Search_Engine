"""
Quick test script for the /api/search endpoint
Tests the complete BM25 + Response Synthesis pipeline
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_signup():
    """Create a test user"""
    response = requests.post(
        f"{BASE_URL}/api/signup",
        json={"username": "testuser", "email": "test@example.com", "password": "test123"}
    )
    if response.status_code == 200:
        print("✓ Signup successful")
        return True
    elif response.status_code == 409:
        print("ℹ User already exists")
        return True
    else:
        print(f"✗ Signup failed: {response.status_code}")
        return False

def test_login():
    """Login to get session cookie"""
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "testuser", "password": "test123"}
    )
    if response.status_code == 200:
        print("✓ Login successful")
        return response.cookies
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_search(cookies, query="rising tech stocks", limit=5):
    """Test the search endpoint"""
    print(f"\nTesting search query: '{query}'")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": query, "limit": limit},
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Search successful")
        print(f"\nResponse Structure:")
        print(f"  - Total Results: {data.get('metadata', {}).get('total_results')}")
        print(f"  - Ranking Method: {data.get('metadata', {}).get('ranking_method')}")
        print(f"  - Query: {data.get('metadata', {}).get('query')}")
        
        print(f"\nTop Results:")
        for i, result in enumerate(data.get('results', [])[:3], 1):
            print(f"\n  {i}. {result.get('symbol')} - {result.get('company_name')}")
            print(f"     Rank: {result.get('rank')} | Score: {result.get('score')}")
            print(f"     Sector: {result.get('sector')}")
            print(f"     Price: ${result.get('metrics', {}).get('price')} ({result.get('metrics', {}).get('change_percent')}%)")
            print(f"     Reasons:")
            for reason in result.get('reasons', [])[:5]:
                print(f"       • {reason}")
        
        return True
    else:
        print(f"✗ Search failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_empty_query(cookies):
    """Test with empty query to get all stocks"""
    print(f"\nTesting empty query (all stocks)")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": "", "limit": 3},
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Empty query successful")
        print(f"  Total Results: {data.get('metadata', {}).get('total_results')}")
        print(f"  Returned {len(data.get('results', []))} stocks")
        return True
    else:
        print(f"✗ Empty query failed: {response.status_code}")
        return False

def test_sector_filter(cookies):
    """Test with sector filter"""
    print(f"\nTesting sector filter (Technology)")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": "rising", "sector": "Technology", "limit": 3},
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Sector filter successful")
        print(f"  Total Results: {data.get('metadata', {}).get('total_results')}")
        for result in data.get('results', [])[:3]:
            print(f"  - {result.get('symbol')}: {result.get('sector')}")
        return True
    else:
        print(f"✗ Sector filter failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("SEARCH ENDPOINT TEST")
    print("=" * 60)
    
    # Step 0: Signup
    test_signup()
    
    # Step 1: Login
    cookies = test_login()
    if not cookies:
        print("\n✗ Cannot proceed without login")
        exit(1)
    
    # Wait a moment for stocks to load
    import time
    print("\nWaiting 5 seconds for stock data to load...")
    time.sleep(5)
    
    # Step 2: Test various search scenarios
    test_search(cookies, "rising tech stocks", limit=5)
    test_search(cookies, "falling energy", limit=3)
    test_search(cookies, "high volume", limit=3)
    test_empty_query(cookies)
    test_sector_filter(cookies)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")

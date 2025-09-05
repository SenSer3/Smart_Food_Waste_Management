import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_endpoint(method, endpoint, data=None, headers=None, auth_token=None):
    """Test a single endpoint and return the result."""
    url = f"{BASE_URL}{endpoint}"
    if auth_token:
        headers = headers or {}
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"status": "ERROR", "message": f"Unsupported method: {method}"}

        return {
            "status": "SUCCESS" if response.status_code < 400 else "ERROR",
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type') == 'application/json' else response.text
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def run_all_tests():
    """Run comprehensive tests for all endpoints."""
    print("🚀 Starting comprehensive endpoint testing...\n")

    results = []

    # Test 1: Food Alternatives
    print("1. Testing Food Alternatives Endpoint")
    result = test_endpoint("POST", "/food-alternatives", {"food_name": "apple"})
    results.append({"test": "Food Alternatives", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 2: Menu Alternatives
    print("2. Testing Menu Alternatives Endpoint")
    result = test_endpoint("POST", "/menu-alternatives", {"menu": ["apple", "banana"]})
    results.append({"test": "Menu Alternatives", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 3: Signup
    print("3. Testing Signup Endpoint")
    result = test_endpoint("POST", "/signup", {"email": "test@example.com", "password": "password123"})
    results.append({"test": "Signup", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 4: Login
    print("4. Testing Login Endpoint")
    result = test_endpoint("POST", "/login", {"username": "test@example.com", "password": "password123"})
    results.append({"test": "Login", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    auth_token = None
    if result["status"] == "SUCCESS" and "access_token" in str(result.get("response", "")):
        try:
            auth_token = result["response"]["access_token"]
            print("   ✅ Auth token obtained")
        except:
            print("   ❌ Could not extract auth token")

    # Test 5: Waste Prediction (Basic)
    print("5. Testing Waste Prediction Endpoint (Basic)")
    waste_data = {
        "user_id": "test_user",
        "recent_waste": [{"quantity": 5}],
        "menu_items": ["apple", "banana"],
        "day_of_week": 1
    }
    result = test_endpoint("POST", "/waste-prediction", waste_data)
    results.append({"test": "Waste Prediction Basic", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 6: Waste Prediction (Edge Cases)
    print("6. Testing Waste Prediction Edge Cases")

    # Empty recent waste
    waste_data_empty = {
        "user_id": "test_user",
        "recent_waste": [{"quantity": 500}],  # Testing large recent waste
        "menu_items": ["apple"],
        "day_of_week": 1
    }
    result = test_endpoint("POST", "/waste-prediction", waste_data_empty)
    results.append({"test": "Waste Prediction Empty Waste", "result": result})
    print(f"   Empty waste: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Empty menu items
    waste_data_no_menu = {
        "user_id": "test_user",
        "recent_waste": [{"quantity": 5}],
        "menu_items": ["Apple","Lemonade"],  # Testing case insensitivity
        "day_of_week": 1
    }
    result = test_endpoint("POST", "/waste-prediction", waste_data_no_menu)
    results.append({"test": "Waste Prediction No Menu", "result": result})
    print(f"   No menu: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Invalid day
    waste_data_invalid_day = {
        "user_id": "test_user",
        "recent_waste": [{"quantity": 5}],
        "menu_items": ["apple"],
        "day_of_week": 0  # Invalid day (should be 0-6)
    }
    result = test_endpoint("POST", "/waste-prediction", waste_data_invalid_day)
    results.append({"test": "Waste Prediction Invalid Day", "result": result})
    print(f"   Invalid day: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 7: Wastage Records (if authenticated)
    if auth_token:
        print("7. Testing Wastage Records Endpoints")

        # Add wastage record
        wastage_data = {
            "user_id": "test_user",
            "date": "2024-01-01",
            "food_item": "apple",
            "quantity": 5.0,
            "notes": "Test waste"
        }
        result = test_endpoint("POST", "/wastage", wastage_data, auth_token=auth_token)
        results.append({"test": "Add Wastage Record", "result": result})
        print(f"   Add wastage: {result['status']} (Code: {result.get('status_code', 'N/A')})")

        # Get wastage records
        result = test_endpoint("GET", "/wastage", auth_token=auth_token)
        results.append({"test": "Get Wastage Records", "result": result})
        print(f"   Get wastage: {result['status']} (Code: {result.get('status_code', 'N/A')})")

        # Get wastage analysis
        result = test_endpoint("GET", "/wastage/analysis", auth_token=auth_token)
        results.append({"test": "Wastage Analysis", "result": result})
        print(f"   Analysis: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    else:
        print("7. Skipping authenticated endpoints (no auth token)")

    # Test 8: Error Handling
    print("8. Testing Error Handling")
    result = test_endpoint("POST", "/waste-prediction", {"user_id": "test"})  # Missing required fields
    results.append({"test": "Waste Prediction Missing Fields", "result": result})
    print(f"   Missing fields: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Summary
    print("\n📊 Test Summary:")
    success_count = sum(1 for r in results if r["result"]["status"] == "SUCCESS")
    total_count = len(results)
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")

    # Detailed results
    print("\n📋 Detailed Results:")
    for test_result in results:
        status_icon = "✅" if test_result["result"]["status"] == "SUCCESS" else "❌"
        print(f"{status_icon} {test_result['test']}: {test_result['result']['status']}")

    return results

if __name__ == "__main__":
    run_all_tests()

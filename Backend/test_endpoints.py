"""
Comprehensive endpoint testing for Smart Food Waste Management Backend
This module provides automated testing for all API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_endpoint(method, endpoint, data=None, headers=None):
    """
    Test a single endpoint and return the result.
    
    Args:
        method (str): HTTP method ('GET' or 'POST')
        endpoint (str): API endpoint path
        data (dict, optional): Request data. Defaults to None.
        headers (dict, optional): Request headers. Defaults to None.
    
    Returns:
        dict: Test result containing status, status code and response
    """
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if endpoint == "/login":  # Special handling for login form data
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
        else:
            return {
                "status": "ERROR", 
                "message": f"Unsupported method: {method}"
            }

        result = {
            "status": "SUCCESS" if response.status_code < 400 else "ERROR",
            "status_code": response.status_code,
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text
            
        if result["status"] == "ERROR":
            print(f"Error response: {result['response']}")
        return result
        
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": str(e)
        }


def run_all_tests():
    """
    Run comprehensive tests for all endpoints.
    Tests food alternatives, menu alternatives, and waste prediction endpoints.
    """
    print("🚀 Starting comprehensive endpoint testing...\n")

    results = []

    # Test 1: Food Alternatives
    print("1. Testing Food Alternatives Endpoint")
    result = test_endpoint(
        "POST", 
        "/food-alternatives", 
        {"food_name": "rice"}
    )
    results.append({"test": "Food Alternatives", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 2: Menu Alternatives
    print("2. Testing Menu Alternatives Endpoint")
    result = test_endpoint(
        "POST", 
        "/menu-alternatives", 
        {"menu": ["rice", "chicken", "vegetables"]}
    )
    results.append({"test": "Menu Alternatives", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")

    # Test 3: Waste Prediction (Basic)
    print("3. Testing Waste Prediction Endpoint (Basic)")
    waste_prediction_data = {
        "user_id": "test_user",
        "recent_waste": [
            {
                "quantity": 2.5,
                "date": datetime.now().isoformat(),
                "food_item": "rice"
            }
        ],
        "menu_items": ["rice", "chicken", "vegetables"],
        "day_of_week": 1
    }
    result = test_endpoint(
        "POST", 
        "/waste-prediction", 
        waste_prediction_data
    )
    results.append({"test": "Waste Prediction Basic", "result": result})
    print(f"   Status: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    if result['status'] == "SUCCESS":
        print(f"   Response: {json.dumps(result['response'], indent=2)}")

    # Test 4: Waste Prediction Edge Cases
    print("4. Testing Waste Prediction Edge Cases")
    
    # Empty waste test
    empty_waste_data = {
        "user_id": "test_user",
        "recent_waste": [],
        "menu_items": ["rice", "chicken"],
        "day_of_week": 1
    }
    result = test_endpoint(
        "POST", 
        "/waste-prediction", 
        empty_waste_data
    )
    print(f"   Empty waste: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    if result['status'] == "SUCCESS":
        print(f"   Response: {json.dumps(result['response'], indent=2)}")
    results.append({"test": "Waste Prediction Empty", "result": result})

    # No menu test
    no_menu_data = {
        "user_id": "test_user",
        "recent_waste": [
            {
                "quantity": 1.0,
                "date": datetime.now().isoformat(),
                "food_item": "rice"
            }
        ],
        "menu_items": [],
        "day_of_week": 1
    }
    result = test_endpoint(
        "POST", 
        "/waste-prediction", 
        no_menu_data
    )
    print(f"   No menu: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    if result['status'] == "SUCCESS":
        print(f"   Response: {json.dumps(result['response'], indent=2)}")
    results.append({"test": "Waste Prediction No Menu", "result": result})

    # Invalid day test
    invalid_day_data = {
        "user_id": "test_user",
        "recent_waste": [
            {
                "quantity": 1.0,
                "date": datetime.now().isoformat(),
                "food_item": "rice"
            }
        ],
        "menu_items": ["rice"],
        "day_of_week": 7  # Invalid day (should be 0-6)
    }
    result = test_endpoint(
        "POST", 
        "/waste-prediction", 
        invalid_day_data
    )
    print(f"   Invalid day: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    results.append({"test": "Waste Prediction Invalid Day", "result": result})

    # Test 5: Missing Fields Validation
    print("5. Testing Error Handling")
    missing_fields_data = {
        "user_id": "test_user"
        # Missing required fields
    }
    result = test_endpoint(
        "POST", 
        "/waste-prediction", 
        missing_fields_data
    )
    print(f"   Missing fields: {result['status']} (Code: {result.get('status_code', 'N/A')})")
    results.append({"test": "Missing Fields Validation", "result": result})

    # Calculate and display test summary
    successful = sum(1 for test in results if test["result"]["status"] == "SUCCESS")
    total = len(results)

    print("\n📊 Test Summary:")
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")

    print("\n📋 Detailed Results:")
    for test in results:
        status = "✅ SUCCESS" if test["result"]["status"] == "SUCCESS" else "❌ FAILED"
        print(f"{status}: {test['test']}")

    return results


if __name__ == "__main__":
    run_all_tests()
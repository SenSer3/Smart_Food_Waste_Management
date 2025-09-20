# Smart Food Waste Management API Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Food Wastage Management](#food-wastage-management)
3. [Food Alternatives](#food-alternatives)
4. [Waste Prediction](#waste-prediction)
5. [Error Handling](#error-handling)
6. [Common Response Codes](#common-response-codes)

## Authentication

### 1. Sign Up
**Endpoint:** `POST /signup`

**Description:** Creates a new user account in the system.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Constraints:**
- Email must be a valid email format
- Password must be provided

**Success Response (201 Created):**
```json
{
    "message": "User signed up successfully. Please check your email to confirm."
}
```

**Error Responses:**
- 400 Bad Request: Invalid email format or password
- 409 Conflict: Email already exists
- 500 Internal Server Error: Server error

### 2. Login
**Endpoint:** `POST /login`

**Description:** Authenticates user and provides access token.

**Request Body (form-data):**
```
username: user@example.com
password: securepassword123
```

**Success Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid credentials
- 500 Internal Server Error: Server error

## Food Wastage Management

### 1. Add Wastage Record
**Endpoint:** `POST /wastage`

**Description:** Records a new food wastage entry.

**Authentication Required:** Yes (Bearer Token)

**Request Body:**
```json
{
    "date": "2025-09-20",
    "food_item": "rice",
    "quantity": 2.5,
    "notes": "Leftover from lunch service"
}
```

**Constraints:**
- date: Optional, ISO format (YYYY-MM-DD)
- food_item: Required, string
- quantity: Required, positive number (in kg)
- notes: Optional, string

**Success Response (200 OK):**
```json
{
    "message": "Wastage record added successfully"
}
```

**Error Responses:**
- 400 Bad Request: Invalid data format
- 401 Unauthorized: Invalid/missing token
- 500 Internal Server Error

### 2. Get Wastage Records
**Endpoint:** `GET /wastage`

**Description:** Retrieves all wastage records for the authenticated user.

**Authentication Required:** Yes (Bearer Token)

**Success Response (200 OK):**
```json
{
    "wastage_records": [
        {
            "id": "1",
            "date": "2025-09-20",
            "food_item": "rice",
            "quantity": 2.5,
            "notes": "Leftover from lunch service"
        },
        // ... more records
    ]
}
```

## Food Alternatives

### 1. Single Food Alternative
**Endpoint:** `POST /food-alternatives`

**Description:** Finds nutritionally similar alternatives for a single food item.

**Request Body:**
```json
{
    "food_name": "rice"
}
```

**Constraints:**
- food_name: Required, non-empty string

**Success Response (200 OK):**
```json
{
    "input_food": "rice",
    "input_food_nutrients": {
        "calories": 130,
        "protein": 2.7,
        "carbs": 28,
        "fat": 0.3
    },
    "nutrients_message": "High in carbohydrates, moderate protein content",
    "alternatives": [
        {
            "food": "quinoa",
            "similarity_score": 0.85,
            "nutrients": {
                "calories": 120,
                "protein": 4.4,
                "carbs": 21,
                "fat": 1.9
            },
            "comparison": "Higher protein, lower carbs"
        },
        // ... more alternatives
    ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Empty food name
- 404 Not Found: Food not found in database
- 500 Internal Server Error

### 2. Menu Alternatives
**Endpoint:** `POST /menu-alternatives`

**Description:** Finds alternatives for multiple food items in a menu.

**Request Body:**
```json
{
    "menu": ["rice", "chicken", "vegetables"]
}
```

**Constraints:**
- menu: Required, non-empty array of strings

**Success Response (200 OK):**
```json
{
    "menu_alternatives": [
        {
            "input_food": "rice",
            "input_food_nutrients": { /* nutrient details */ },
            "alternatives": [ /* alternatives for rice */ ]
        },
        {
            "input_food": "chicken",
            "input_food_nutrients": { /* nutrient details */ },
            "alternatives": [ /* alternatives for chicken */ ]
        },
        // ... alternatives for each menu item
    ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Invalid menu format
- 500 Internal Server Error

## Waste Prediction

### Predict Waste
**Endpoint:** `POST /waste-prediction`

**Description:** Predicts future food waste based on historical data and current inputs.

**Request Body:**
```json
{
    "user_id": "user123",
    "recent_waste": [
        {
            "quantity": 2.5,
            "date": "2025-09-20T00:00:00",
            "food_item": "rice"
        }
    ],
    "menu_items": ["rice", "chicken", "vegetables"],
    "day_of_week": 1
}
```

**Constraints:**
- user_id: Required, string
- recent_waste: Array of waste records
  - quantity: Positive number (kg)
  - date: ISO datetime string
  - food_item: String
- menu_items: Array of strings
- day_of_week: Integer 0-6 (0=Sunday, 6=Saturday)

**Success Response (200 OK):**
```json
{
    "prediction": {
        "predicted_waste_kg": 3.25,
        "confidence_level": "medium"
    },
    "analysis": {
        "recent_waste_total_kg": 2.5,
        "recent_waste_average_kg": 2.5,
        "menu_item_count": 3,
        "day_of_week": 1,
        "trend": "increasing",
        "historical": {
            "weekly_waste": {
                "2025-09-13": 15.2,
                "2025-09-20": 17.8
            },
            "waste_by_item": {
                "rice": 8.5,
                "chicken": 5.2,
                "vegetables": 4.1
            },
            "high_waste_items": {
                "rice": 8.5,
                "chicken": 5.2
                // Top 5 wasted items
            }
        }
    },
    "visualizations": {
        "weekly_trend": "base64_encoded_image",
        "waste_by_item": "base64_encoded_image"
    }
}
```

**Calculation Details:**
1. Recent Waste Analysis:
   - Totals the quantities from recent_waste
   - Calculates average waste per record
   - Identifies trends (increasing/decreasing)

2. Menu Impact:
   - Number of items affects prediction
   - More items typically indicate higher potential waste
   - Default estimate: 100 portions per menu item

3. Day of Week Effect:
   - Historical patterns by day are considered
   - Weekend vs weekday patterns
   - Special events on specific days

4. Visualization Details:
   - Weekly Trend Chart:
     - X-axis: Last 4 weeks
     - Y-axis: Total waste in kg
     - Line chart with trend indicators
   - Waste by Item Chart:
     - X-axis: Food items
     - Y-axis: Total waste in kg
     - Bar chart showing top waste contributors

**Edge Cases:**
1. Empty Recent Waste:
   - Handles new users with no history
   - Uses default baseline predictions
   - Lower confidence level in prediction

2. No Menu Items:
   - Uses minimum baseline prediction
   - Adjusts based on day of week only
   - Marks prediction as limited accuracy

3. Invalid Day:
   - Returns 422 error if day < 0 or day > 6
   - Requires valid integer input

**Error Responses:**
- 422 Unprocessable Entity:
  ```json
  {
    "detail": "day_of_week must be an integer between 0 and 6 inclusive"
  }
  ```
- 400 Bad Request: Invalid data format
- 500 Internal Server Error: Model prediction failure

## Error Handling

### Common Error Response Format
```json
{
    "detail": "Error message describing the issue"
}
```

### Validation Errors
```json
{
    "detail": [
        {
            "loc": ["body", "field_name"],
            "msg": "Field specific error message",
            "type": "error_type"
        }
    ]
}
```

## Common Response Codes

- 200 OK: Successful operation
- 201 Created: Resource successfully created
- 400 Bad Request: Invalid input data
- 401 Unauthorized: Missing or invalid authentication
- 404 Not Found: Resource not found
- 422 Unprocessable Entity: Input validation failed
- 500 Internal Server Error: Server-side error

## Authentication Headers

For protected endpoints, include the JWT token in the Authorization header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Rate Limiting

- 100 requests per minute per IP address
- 1000 requests per hour per user

## Best Practices

1. Always validate input data before sending
2. Handle all error responses in your frontend
3. Implement proper token storage and refresh mechanisms
4. Cache frequently accessed data
5. Implement retry logic for failed requests
6. Monitor response times and implement loading states
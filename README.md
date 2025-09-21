# Smart Food Waste Management - Project Overview

This project is a backend API service for Smart Food Waste Management, designed to help users reduce food waste by providing food alternatives and menu suggestions based on nutritional data.

## Hosted API Base URL

The API is hosted at:  
https://food-management-backend-z51f.onrender.com

## Core Features

### Food Alternatives Endpoint

- **POST /food-alternatives**  
  Provides alternative food suggestions for a given food item.  
  **Request:**  
  ```json
  {
    "food_name": "chicken"
  }
  ```  
  **Response:**  
  Returns a list of alternative foods with nutritional information and similarity scores.

### Menu Alternatives Endpoint

- **POST /menu-alternatives**  
  Provides alternative suggestions for a list of menu items.  
  **Request:**  
  ```json
  {
    "menu": ["chicken", "rice", "potato"]
  }
  ```  
  **Response:**  
  Returns alternatives for each menu item in the list, including nutritional details.

## Usage

Users can access the API endpoints by sending HTTP POST requests to the hosted URL with the appropriate JSON payloads as shown above.

## Notes

- This overview focuses on the food and menu alternative endpoints, which are the primary features currently in use.
- The API is built using FastAPI and leverages machine learning models for food similarity and nutritional analysis.
- Stay tuned for future updates including waste prediction and user management features.

## Contact

For more information or support, please contact the development team.
